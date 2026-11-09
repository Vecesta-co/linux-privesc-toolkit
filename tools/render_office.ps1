param(
    [Parameter(Mandatory=$true)][ValidateSet('docx','pptx')][string]$Kind,
    [Parameter(Mandatory=$true)][string]$InputPath,
    [Parameter(Mandatory=$true)][string]$OutputPath
)

$resolvedInput = (Resolve-Path -LiteralPath $InputPath).Path
$outputFull = [System.IO.Path]::GetFullPath($OutputPath)
$outputDir = Split-Path -Parent $outputFull
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

if ($Kind -eq 'docx') {
    $word = $null
    $document = $null
    try {
        $word = New-Object -ComObject Word.Application
        $word.Visible = $false
        $word.DisplayAlerts = 0
        $document = $word.Documents.Open($resolvedInput, $false, $true)
        [void]$document.Fields.Update()
        $document.ExportAsFixedFormat($outputFull, 17)
        Write-Output "Exported PDF: $outputFull"
    }
    finally {
        if ($document -ne $null) { $document.Close(0) | Out-Null; [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($document) }
        if ($word -ne $null) { $word.Quit(); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) }
        [GC]::Collect(); [GC]::WaitForPendingFinalizers()
    }
}
else {
    $presentationApp = $null
    $presentation = $null
    try {
        $presentationApp = New-Object -ComObject PowerPoint.Application
        $presentationApp.Visible = 0
        $presentation = $presentationApp.Presentations.Open($resolvedInput, $true, $false, $false)
        $presentation.Export($outputDir, 'PNG', 1920, 1080)
        $slides = Get-ChildItem -LiteralPath $outputDir -Filter 'Slide*.PNG' | Sort-Object { [int]($_.BaseName -replace '\D','') }
        $index = 1
        foreach ($slide in $slides) {
            $destination = Join-Path $outputDir ('slide-{0:D2}.png' -f $index)
            Move-Item -LiteralPath $slide.FullName -Destination $destination -Force
            $index++
        }
        Write-Output "Exported $($slides.Count) slides to $outputDir"
    }
    finally {
        if ($presentation -ne $null) { $presentation.Close(); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($presentation) }
        if ($presentationApp -ne $null) { $presentationApp.Quit(); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($presentationApp) }
        [GC]::Collect(); [GC]::WaitForPendingFinalizers()
    }
}
