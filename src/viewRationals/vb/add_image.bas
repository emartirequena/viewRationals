Attribute VB_Name = "Módulo2"
Sub CreateChart()
Attribute CreateChart.VB_ProcData.VB_Invoke_Func = " \n14"
'
' Macro2 Macro
'
' Acceso directo: CTRL+a
'
    init_row = ActiveCell.Row
    end_row = init_row + 12
    ran = "A" & init_row & ":M" & end_row
    Range(ran).Select
    ActiveSheet.Shapes.AddChart2(307, xlSurfaceTopView).Select
    ActiveChart.SetSourceData Source:=Range(ran)
    chart_name = Right(ActiveChart.Name, Len(ActiveChart.Name) - 2)
    
    ActiveChart.Parent.Cut
    Range("Q" & init_row).Select
    ActiveSheet.Paste
    chart_name = Right(ActiveChart.Name, Len(ActiveChart.Name) - 2)
    
    
    ActiveSheet.ChartObjects(chart_name).Activate
    ActiveChart.ChartTitle.Select
    Selection.Delete
    ActiveSheet.ChartObjects(chart_name).Activate
    ActiveChart.Axes(xlSeries).Select
    Selection.Delete
    ActiveSheet.ChartObjects(chart_name).Activate
    ActiveChart.Axes(xlCategory).Select
    Selection.Delete
    ActiveSheet.ChartObjects(chart_name).Activate
    ActiveChart.Legend.Select
    Selection.Delete
    ActiveSheet.ChartObjects(chart_name).Activate
    ActiveSheet.Shapes(chart_name).ScaleWidth 0.6680555556, msoFalse, _
        msoScaleFromTopLeft
    ActiveSheet.ChartObjects(chart_name).Activate
    ActiveSheet.Shapes(chart_name).Line.Visible = msoFalse
        
    ran = "A" & (init_row + 19)
    Range(ran).Select
End Sub

Sub Macro2()
Attribute Macro2.VB_ProcData.VB_Invoke_Func = "a\n14"
    While Not IsEmpty(ActiveCell)
        CreateChart
    Wend
End Sub
