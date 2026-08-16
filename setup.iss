; Script Inno Setup — VentoyIsoUpdater
; Génère un installateur Windows professionnel avec :
;   - Raccourci menu Démarrer
;   - Raccourci bureau (optionnel)
;   - Entrée dans "Applications installées" (Ajout/Suppression de programmes)
;   - Désinstallateur propre
;
; Prérequis : Inno Setup 6+ (https://jrsoftware.org/isinfo.php)
; Usage (sur Windows) : clic droit → Compile, ou iscc setup.iss

#define AppName      "VentoyIsoUpdater"
; surchargeable : iscc /DAppVersion=1.2.3 setup.iss
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#define AppPublisher "Maxence Baffet (celmax)"
#define AppURL       "https://github.com/celmax85"
#define AppExeName   "VentoyIsoUpdater.exe"
#define AppDesc      "Gestionnaire graphique de clés USB Ventoy"

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
; Compression maximale
Compression=lzma2/ultra64
SolidCompression=yes
; Icône de l'installateur
WizardStyle=modern
; L'installateur ne nécessite pas les droits admin (installe dans AppData si refusé)
PrivilegesRequiredOverridesAllowed=dialog
; Fichier de sortie
OutputDir=dist\windows
OutputBaseFilename={#AppName}-{#AppVersion}-windows-setup
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}

[Languages]
Name: "french";    MessagesFile: "compiler:Languages\French.isl"
Name: "english";   MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";    Description: "Créer un raccourci sur le bureau";    GroupDescription: "Raccourcis supplémentaires :"; Flags: unchecked

[Files]
; Binaire principal
Source: "dist\windows\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Menu Démarrer
Name: "{group}\{#AppName}";                  Filename: "{app}\{#AppExeName}"
Name: "{group}\Désinstaller {#AppName}";     Filename: "{uninstallexe}"
; Bureau (optionnel, coché par l'utilisateur)
Name: "{autodesktop}\{#AppName}";            Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; Propose de lancer l'appli à la fin de l'installation
Filename: "{app}\{#AppExeName}"; \
    Description: "Lancer {#AppName}"; \
    Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Supprime les fichiers de config à la désinstallation (optionnel — commenter si indésirable)
; Type: filesandordirs; Name: "{userappdata}\ventoyisoupdater"
