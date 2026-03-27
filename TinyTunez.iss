[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; To generate a new GUID, use Tools > Generate GUID inside the IDE.
AppId={{8B5A2D3E-4F7C-4A8B-9D2E-3F9A8B7C6D5E}}

AppName=TinyTunez
AppVersion=1.0.0
;AppVerName=TinyTunez 1.0.0
AppPublisher=TinyTunez
AppPublisherURL=https://github.com/lilshorty83/TinyTunez
AppSupportURL=https://github.com/lilshorty83/TinyTunez
AppUpdatesURL=https://github.com/lilshorty83/TinyTunez
DefaultDirName={pf}\TinyTunez
DefaultGroupName=TinyTunez
AllowNoIcons=yes
LicenseFile=LICENSE.txt
OutputDir=installer
OutputBaseFilename=TinyTunez-Setup
SetupIconFile=assets\icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\TinyTunez.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\TinyTunez"; Filename: "{app}\TinyTunez.exe"; IconFilename: "{app}\assets\icon.ico"; WorkingDir: "{app}"
Name: "{group}\Uninstall TinyTunez"; Filename: "{uninstallexe}"
Name: "{userdesktop}\TinyTunez"; Filename: "{app}\TinyTunez.exe"; IconFilename: "{app}\assets\icon.ico"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\TinyTunez.exe"; Description: "{cm:LaunchProgram,TinyTunez}"; Flags: nowait postinstall skipifsilent

[Code]
// Function to check if Visual C++ Redistributable is installed
function IsVCRedistInstalled: Boolean;
var
  ResultCode: Integer;
begin
  // Check for Visual C++ 2015-2022 Redistributable (x64)
  Result := RegKeyExists(HKLM, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{d992c24e-e3f2-4ce2-bcd8-8b0f2b8e5e2a}');
  if not Result then
    // Check for alternative version
    Result := RegKeyExists(HKLM, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{e2803110-78b3-4d10-b2c0-39711846a497}');
end;

// Install Visual C++ Redistributable if needed
procedure InstallVCRedist;
var
  ResultCode: Integer;
begin
  if not IsVCRedistInstalled then
  begin
    // Download and install Visual C++ Redistributable
    // Note: You'll need to include the VCRedist installer in your setup files
    // or download it during installation
  end;
end;

// Custom setup page for additional options
function ShouldInstallDesktopIcon: Boolean;
begin
  Result := IsTaskSelected('desktopicon');
end;

// Initialize setup
function InitializeSetup(): Boolean;
begin
  Result := True;
  
  // Check Windows version
  if not UsingWinNT then
  begin
    MsgBox('TinyTunez requires Windows NT or later.', mbError, MB_OK);
    Result := False;
  end;
  
  // Check for .NET Framework (if needed)
  // Note: Python apps usually don't need .NET Framework
end;

// Post-install cleanup
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Create user data directory in AppData
    CreateDir(ExpandConstant('{userappdata}\TinyTunez'));
  end;
end;
