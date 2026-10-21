; Inno Setup Script for Bongo on Windows (x64 and ARM64)
; Builds professional standalone setup installer (Bongo-Setup-1.1.0.exe)

#define MyAppName "Bongo"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "Bongo Team"
#define MyAppURL "https://getbongo.app"
#define MyAppExeName "bongo.exe"
#define MyAppSettingsExeName "bongo-settings.exe"

[Setup]
AppId={{9F7B3E22-5F16-4B82-B2D9-B3F7368D149E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=..\..\..\LICENSE
OutputDir=..\release
OutputBaseFilename=Bongo-Setup-{#MyAppVersion}
SetupIconFile=..\data\bongo.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "autostart"; Description: "Start Bongo automatically when Windows boots"; GroupDescription: "Windows Integration:"

[Files]
Source: "..\build\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\build\{#MyAppSettingsExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\build\bongo_engine.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\data\bongo.ico"; DestDir: "{app}\data"; Flags: ignoreversion
Source: "..\data\bongo.png"; DestDir: "{app}\data"; Flags: ignoreversion
Source: "..\data\bongo_32.png"; DestDir: "{app}\data"; Flags: ignoreversion
Source: "..\..\..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\..\THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppSettingsExeName}"; IconFilename: "{app}\data\bongo.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppSettingsExeName}"; IconFilename: "{app}\data\bongo.ico"; Tasks: desktopicon
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppSettingsExeName}"; IconFilename: "{app}\data\bongo.ico"
Name: "{group}\{#MyAppName} Settings"; Filename: "{app}\{#MyAppSettingsExeName}"; IconFilename: "{app}\data\bongo.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "Bongo"; ValueData: """{app}\{#MyAppExeName}"" --daemon"; Tasks: autostart; Flags: uninsdeletevalue

[Run]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--daemon"; Flags: nowait runhidden
Filename: "{app}\{#MyAppSettingsExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
