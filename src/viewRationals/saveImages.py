import os
import re
import shutil
import math
from multiprocessing import Pool, cpu_count
from threading import Lock
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from madcad import vec3, settings
import traceback
from gc import collect

from views import ViewRender
from getObjects import get_objects
from utils import make_video
from timing import timing
from color import _convert_color

settings_file = 'settings.txt'
mutex = Lock()


def _del_folder(folder):
    if not os.path.exists(folder):
        return
    names = os.listdir(folder)
    for name in names:
        path = os.path.join(folder, name)
        if os.path.isdir(path):
            _del_folder(path)
        else:
            os.remove(path)
    os.rmdir(folder)


def _makePath(accumulate, factors, image_path, dim_str, period, number, single_image=False, subfolder=''):
    if accumulate:
        if not single_image:
            path = os.path.join(image_path, f'P{period:02d}', dim_str, 'Accumulate', f'N{number:d}_F{factors}', subfolder)
        else:
            path = os.path.join(image_path, 'Snapshots', dim_str, 'Accumulate', subfolder)
    else:
        if not single_image:
            path  = os.path.join(image_path, f'P{period:02d}', dim_str, f'N{number:d}_F{factors}', subfolder)
        else:
            path = os.path.join(image_path, 'Snapshots', dim_str, 'Not Accumulate', subfolder)
    if os.path.exists(path):
        if not single_image:
            _del_folder(path)
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def _get_last_frame(filename):
    """
    Dado un nombre de fichero con frame, busca todos los ficheros en el mismo directorio
    que coincidan y devuelve el número de frame más alto.
    """
    basedir, fname = os.path.split(filename)
    # Extrae el patrón base y extensión
    match = re.match(r'^(.*?)(\d+)\.(\w+)$', fname)
    if not match:
        return 0
    base_pattern = match.group(1)
    ext = match.group(3)
    # Regex para buscar el frame
    frame_regex = re.compile(rf'^{re.escape(base_pattern)}(\d+)\.{re.escape(ext)}$')
    max_frame = 0
    for file in os.listdir(basedir):
        m = frame_regex.match(file)
        if m:
            try:
                frame = int(m.group(1))
                if frame > max_frame:
                    max_frame = frame
            except ValueError:
                continue
    return max_frame


def _get_number_img(number, period, ptime, config):
    background = (*[int(x) for x in config.get('background_color')], 255)
    img = Image.new('RGBA', (500, 40), background)
    draw = ImageDraw.Draw(img)
    string = f'number: {number:,.0f} period: {period:02d} time: {ptime}'.replace(',', '.')
    width = int(draw.textlength(string) + 10)
    img.resize((width, 40))
    font = ImageFont.FreeTypeFont('NotoMono-Regular.ttf', size=24)
    foreground = (*(int(255-x) for x in background[:3]), 255)
    draw.text((0, 0), string, font=font, fill=foreground)
    return img


def _create_image(args):
    view_type, shr_projection, shr_navigation, frame, factor, init_time, prefix, suffix, \
    config, ccolor, spacetime, rationals, dim, number, period, factors, accumulate, dim_str, \
    view_objects, view_time, view_next_number, max_time, \
    image_resx, image_resy, path, rotate, dx, center, center_time, shr_num_video_frames, legend, single_imgae = args

    print(f'------- create image')

    settings.load(settings_file)
    settings.display['background_color'] = vec3(*_convert_color(config.get('background_color')))

    view = ViewRender(view_type)
    view.set_projection(shr_projection.value)
    view.set_navigation(shr_navigation.value)
    if rotate:
        view.rotateTo3DVideo(dx)

    ptime = init_time + frame // factor

    if center:
        p = ptime * np.array(center) / center_time
        view.moveTo(p[0], p[1], p[2])

    view_cells = spacetime[ptime]

    mutex.acquire()
    try:
        objs, _, _ = get_objects(view_cells, number, dim, accumulate, rationals, config, ccolor, 
                                 view_objects, view_time, view_next_number, max_time, ptime, 1)
    except Exception as e:
        print(f'ERROR creating objs: {str(e)}')
        print(traceback.print_exc())
        raise e
    
    mutex.release()
    if not objs:
        print('------ NOT OBJS')
        return

    mutex.acquire()
    try:
        img = view.render(image_resx, image_resy, objs)
    except Exception as e:
        print(f'ERROR rendering image: {str(e)}')
        print(traceback.print_exc())
        raise e

    mutex.release()
    if not img:
        print('------- NOT IMG')
        return
    
    accum_str = ''
    if accumulate:
        accum_str = 'Accum_'

    if legend:
        number_img = _get_number_img(number, period, ptime, config)
        img.alpha_composite(number_img, (10, image_resy - 40))
        del number_img

    file_name = f'{accum_str}{prefix}{dim_str}_N{int(number)}_P{int(period):02d}_F{factors}{suffix}.{frame:04d}.png'
    if single_imgae:
        frame = _get_last_frame(os.path.join(path, file_name))
        frame += 1
        file_name = f'{accum_str}{prefix}{dim_str}_N{int(number)}_P{int(period):02d}_F{factors}{suffix}.{frame:04d}.png'

    print(f'------- save: {file_name}, time: {ptime}')
    shr_num_video_frames.value += 1

    fname = os.path.join(path, file_name)
    try:
        img.save(fname)
    except Exception as e:
        print(f'ERROR saving image {fname}: {str(e)}')
        raise e

    del args
    del objs
    del view
    del img
    collect()

    return


def _create_video(args):
    print('------- CREATING VIDEO')

    path, image_resx, image_resy, frame_rate, \
    prefix, suffix, config, \
    number, period, factors, accumulate, dim_str,\
    shr_num_video_frames, clean_images = args

    shr_num_video_frames.value = -1

    ffmpeg_path = config.get('ffmpeg_path')
    video_path = config.get('video_path')
    video_format = config.get('video_format')
    video_codec = config.get('video_codec')
    bit_rate = config.get('bit_rate')

    accum_str = ''
    if accumulate:
        accum_str = 'Accum_'

    in_sequence_name = os.path.join(path, f'{accum_str}{prefix}{dim_str}_N{number}_P{period:02d}_F{factors}{suffix}.%04d.png')
    main_video_name = os.path.join(path, f'{accum_str}{prefix}{dim_str}_N{number:d}_P{period:02d}_F{factors}{suffix}.{video_format}')
    result = make_video(
        ffmpeg_path, 
        in_sequence_name, main_video_name, 
        video_codec, video_format, 
        frame_rate, bit_rate, 
        image_resx, image_resy
    )
    if not result:
        print('------- ERROR: Error creating video')
        return

    out_video_path = os.path.join(video_path, f'{dim_str}')
    if not os.path.exists(out_video_path):
        os.makedirs(out_video_path)
    dest_video_name = os.path.join(out_video_path, f'{accum_str}{prefix}{dim_str}_N{number:d}_P{period:02d}_F{factors}{suffix}.{video_format}')
    print(f'------- copying {main_video_name} \n-------      to {dest_video_name}')
    shutil.copyfile(main_video_name, dest_video_name)

    if clean_images:
        _del_folder(path)

    del args
    collect()


def _error_callback(val):
    print(f'ERROR: {str(val)}')
    print(traceback.print_exc())

@timing
def _saveImages(args):

    shr_projection, shr_navigation, image_path, init_time, end_time, frame_rate, \
    subfolder, prefix, suffix, num_frames, turn_angle, config, \
    ccolor, view_type, spacetime, rationals, dim, number, period, factors, \
    accumulate, dim_str, view_objects, view_time, view_next_number, \
    max_time, shr_num_video_frames, clean_images, center, center_time, num_cpus, \
    legend, image_resx, image_resy = args
    
    number = int(number)
    period = int(period)

    if prefix and prefix[-1] != '_':
        prefix = prefix + '_'

    if suffix and suffix[0] != '_':
        suffix = '_' + suffix

    single_image = True if num_frames == 1 else False
    try:
        path = _makePath(accumulate, factors, image_path, dim_str, period, number, single_image, subfolder)
    except Exception as e:
        print(f'ERROR: {str(e)}')

    if num_frames == 0:
        num_frames = end_time - init_time + 1

    factor = 1
    if init_time < end_time:
        factor = 1 + num_frames // (end_time - init_time + 1)
    else:
        factor = num_frames

    if num_frames == 1 and init_time == end_time:
        range_frames = 1
    else:
        range_frames = num_frames + 1

    params = []
    for frame in range(range_frames):
        rotate = False
        dx = shr_navigation.value.yaw / math.pi
        if turn_angle > 0:
            k = 0.005 * 400. / 360.
            dx += frame * k * float(turn_angle) / float(num_frames)
            rotate = True
        params.append((
            view_type, shr_projection, shr_navigation, frame, factor, init_time, prefix, suffix,
            config, ccolor, spacetime, rationals, dim, number, period, factors, accumulate, dim_str,
            view_objects, view_time, view_next_number, max_time,
            image_resx, image_resy, path, rotate, dx, center, center_time, shr_num_video_frames, legend,
            single_image
        ))

    args_video = (
        path, image_resx, image_resy, frame_rate,
        prefix, suffix, config,
        number, period, factors, accumulate, dim_str,
        shr_num_video_frames, clean_images
    ) if not single_image else ()

    chunksize = (range_frames // num_cpus) or 1
    print(f'>>>>>>> range_frames: {range_frames}, num_cpus: {num_cpus}, chunksize: {chunksize}')
    
    pool = Pool(num_cpus)
    pool.map_async(func=_create_image, iterable=params, chunksize=chunksize, error_callback=_error_callback)

    return (pool, args_video)
