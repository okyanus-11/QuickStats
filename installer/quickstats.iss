#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif

#define MyAppName "QuickStats"
#define MyAppPublisher "Okyanus Bora Sevik"
#define MyAppExeName "QuickStats.exe"

[Setup]
AppId={{6B8B9A9A-57F5-4A90-8C13-2F1C8E9B7A41}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
LicenseFile=..\LICENSE
OutputDir=..\dist\installer
OutputBaseFilename=QuickStats-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\QuickStats\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\QuickStats"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall QuickStats"; Filename: "{uninstallexe}"
Name: "{autodesktop}\QuickStats"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch QuickStats"; Flags: postinstall nowait skipifsilent
