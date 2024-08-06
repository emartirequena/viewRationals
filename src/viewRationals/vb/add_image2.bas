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
    
    ActiveChart.Parent.Cut
    Range("Q" & init_row).Select
    ActiveSheet.Paste
    

    chart_name = Right(ActiveChart.Name, Len(ActiveChart.Name) - Len(ActiveSheet.Name) - 1)
    
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
    While Not IsEmpty(ActiveCell)
        CreateChart
        GoToNextHiphen
    Wend
End Sub


