$env:PATH = "$PSScriptRoot\.tools\node;$PSScriptRoot\.tools\node\node_modules\.bin;" + $env:PATH
& "$PSScriptRoot\.tools\node\firebase.cmd" deploy --only hosting
