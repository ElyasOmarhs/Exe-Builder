[Setup]
AppName=Elyas Pashto Scraper
AppVersion=1.0
DefaultDirName={autopf}\ElyasScraper
DefaultGroupName=Elyas Scraper
OutputBaseFilename=ElyasScraper_Setup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64

[Files]
; دا هغه فایل دی چې PyInstaller یې جوړوي
Source: "dist\XsraperPs.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Elyas Scraper"; Filename: "{app}\XsraperPs.exe"
Name: "{commondesktop}\Elyas Scraper"; Filename: "{app}\XsraperPs.exe"
