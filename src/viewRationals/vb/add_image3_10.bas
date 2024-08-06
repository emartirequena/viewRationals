Attribute VB_Name = "Módulo2"

Sub CreateChart(fila As Integer, col As Integer)
Attribute CreateChart.VB_ProcData.VB_Invoke_Func = " \n14"
'
' Macro2 Macro
'
' Acceso directo: CTRL+a
'
    init_row = ActiveCell.Row
    end_row = init_row + 10
    ran = "A" & init_row & ":K" & end_row
    Range(ran).Select
    ActiveSheet.Shapes.AddChart2(307, xlSurfaceTopView).Select
    ActiveChart.SetSourceData Source:=Range(ran)
    
    ActiveChart.Parent.Cut
    Range("Q" & init_row).Select
    ActiveSheet.Paste
    
    chart_name = Right(ActiveChart.Name, Len(ActiveChart.Name) - Len(ActiveSheet.Name) - 1)
    
    ws_name = "mode " & Right(ActiveSheet.Name, 1)
    
    Worksheets(ws_name).ChartObjects(chart_name).Activate
    ActiveChart.ChartTitle.Select
    Selection.Delete
    
    Worksheets(ws_name).ChartObjects(chart_name).Activate
    ActiveChart.Axes(xlSeries).Select
    Selection.Delete

    Worksheets(ws_name).ChartObjects(chart_name).Activate
    ActiveChart.Axes(xlCategory).Select
    Selection.Delete
    
    Worksheets(ws_name).ChartObjects(chart_name).Activate
    ActiveChart.Legend.Select
    Selection.Delete
    
    Worksheets(ws_name).ChartObjects(chart_name).Activate
    Worksheets(ws_name).Shapes(chart_name).ScaleWidth 0.6680555556, msoFalse, _
        msoScaleFromTopLeft
    Worksheets(ws_name).ChartObjects(chart_name).Activate
    Worksheets(ws_name).Shapes(chart_name).Line.Visible = msoFalse
    
    Worksheets(ws_name).ChartObjects(chart_name).Activate
    ActiveChart.ChartArea.Copy
    
    ws_name = "grid " & Right(ActiveSheet.Name, 1)
    Worksheets(ws_name).Paste Destination:=Worksheets(ws_name).Cells(fila, col)
    
End Sub

Sub GoToNextHiphen()
    Count = 0
    While True
        ran = "A" & (ActiveCell.Row + 1)
        Range(ran).Select

        If ActiveCell.Value = "-" Then
            ran = "A" & (ActiveCell.Row + 1)
            Range(ran).Select
            Exit Sub
        End If
        If IsEmpty(ActiveCell) Then
            Count = Count + 1
            If Count > 5 Then
                Exit Sub
            End If
        Else
            Count = 0
        End If
    Wend
End Sub

Sub Macro2()
Attribute Macro2.VB_ProcData.VB_Invoke_Func = "a\n14"
    ws_name = "grid " & Right(ActiveSheet.Name, 1)
    fila = CInt(Worksheets(ws_name).Range("a1").Value)
    col = CInt(Worksheets(ws_name).Range("a2").Value)
    While Not IsEmpty(ActiveCell)
        CreateChart fila * 15 + 1, col * 5 + 1
        GoToNextHiphen
        col = col + 1
        If col = 6 Then
            col = 0
            fila = fila + 1
        End If
        Worksheets(ws_name).Range("a1").Value = fila
        Worksheets(ws_name).Range("a2").Value = col
    Wend
End Sub


