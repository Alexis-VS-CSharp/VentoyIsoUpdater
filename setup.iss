; Inno Setup script — VentoyIsoUpdater
; Generates a professional Windows installer with:
;   - Start menu shortcut
;   - Desktop shortcut (optional)
;   - Entry in "Installed Applications" (Add/Remove Programs)
;   - Clean uninstaller
;
; Requires: Inno Setup 6+ (https://jrsoftware.org/isinfo.php)
; Usage (on Windows): right-click -> Compile, or iscc setup.iss

#define AppName      "VentoyIsoUpdater"
; overridable: iscc /DAppVersion=1.2.3 setup.iss
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#define AppPublisher "Maxence Baffet (celmax)"
#define AppURL       "https://github.com/celmax85"
#define AppExeName   "VentoyIsoUpdater.exe"
#define AppDesc      "Desktop GUI for managing Ventoy USB drives"

[Setup]
AppId={{A3F2C1D8-4B5E-4F6A-9C2D-1E3F5A7B9C0D}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
; Maximum compression
Compression=lzma2/ultra64
SolidCompression=yes
; Installer icon
WizardStyle=modern
; The installer doesn't require admin rights (installs into AppData if refused)
PrivilegesRequiredOverridesAllowed=dialog
; Output file
OutputDir=dist\windows
OutputBaseFilename={#AppName}-{#AppVersion}-windows-setup
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}

[Languages]
Name: "french";    MessagesFile: "compiler:Languages\French.isl"
Name: "english";   MessagesFile: "compiler:Default.isl"

; Custom labels below aren't part of Inno Setup's built-in translations,
; so they're localized by hand here to follow whichever [Languages] entry
; the user picks in the wizard.
[CustomMessages]
french.DesktopIconDesc=Créer un raccourci sur le bureau
english.DesktopIconDesc=Create a desktop shortcut
french.AdditionalIcons=Raccourcis supplémentaires :
english.AdditionalIcons=Additional shortcuts:
french.UninstallIconName=Désinstaller {#AppName}
english.UninstallIconName=Uninstall {#AppName}
french.LaunchAfterInstall=Lancer {#AppName}
english.LaunchAfterInstall=Launch {#AppName}

[Tasks]
Name: "desktopicon";    Description: "{cm:DesktopIconDesc}";    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main binary
Source: "dist\windows\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start menu
Name: "{group}\{#AppName}";                  Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallIconName}";       Filename: "{uninstallexe}"
; Desktop (optional, checked by the user)
Name: "{autodesktop}\{#AppName}";            Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; Offers to launch the app at the end of installation
Filename: "{app}\{#AppExeName}"; \
    Description: "{cm:LaunchAfterInstall}"; \
    Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Removes config files on uninstall (optional — comment out if undesired)
; Type: filesandordirs; Name: "{userappdata}\ventoyisoupdater"
