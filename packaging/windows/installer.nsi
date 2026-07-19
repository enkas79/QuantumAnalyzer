; NSIS installer script for QuantumAnalyzer.
; Built by CI against the PyInstaller onedir output at dist\QuantumAnalyzer\
; (a proper installed-app folder, not a self-extracting onefile exe).
; Version comes from the command line: makensis /DVERSION=1.2.3 installer.nsi

!ifndef VERSION
  !define VERSION "0.0.0"
!endif

Name "QuantumAnalyzer"
; Relative paths in this script (OutFile, File) resolve against the
; script's own directory (packaging/windows), not makensis's invocation
; cwd. Keep this bare so it lands next to this script, where the
; workflow's upload-artifact step expects it.
OutFile "QuantumAnalyzer-Setup-${VERSION}.exe"
InstallDir "$PROGRAMFILES64\QuantumAnalyzer"
RequestExecutionLevel admin

Page directory
Page instfiles

UninstPage uninstConfirm
UninstPage instfiles

Section "Install"
    SetOutPath "$INSTDIR"
    File /r "..\..\dist\QuantumAnalyzer\*.*"
    CreateDirectory "$SMPROGRAMS\QuantumAnalyzer"
    CreateShortcut "$SMPROGRAMS\QuantumAnalyzer\QuantumAnalyzer.lnk" "$INSTDIR\QuantumAnalyzer.exe"
    CreateShortcut "$DESKTOP\QuantumAnalyzer.lnk" "$INSTDIR\QuantumAnalyzer.exe"
    WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
    RMDir /r "$INSTDIR"
    Delete "$SMPROGRAMS\QuantumAnalyzer\QuantumAnalyzer.lnk"
    RMDir "$SMPROGRAMS\QuantumAnalyzer"
    Delete "$DESKTOP\QuantumAnalyzer.lnk"
SectionEnd
