{ self, inputs, ... }: {
   
   flake.nixosModules.mainConfiguration = { pkgs, lib, ...}: {
      imports = [
         self.nixosModules.mainHardware
	self.nixosModules.niri
      ];

  # Bootloader.
  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = true;

  networking.hostName = "m1y"; # Define your hostname.
  # networking.wireless.enable = true;  # Enables wireless support via wpa_supplicant.

  # Configure network proxy if necessary
  # networking.proxy.default = "http://user:password@proxy:port/";
  # networking.proxy.noProxy = "127.0.0.1,localhost,internal.domain";

  # Enable networking
  networking.networkmanager.enable = true;

  # Set your time zone.
  time.timeZone = "Europe/Vilnius";

  # Select internationalisation properties.
  i18n.defaultLocale = "en_US.UTF-8";

  # Enable the X11 windowing system.
  services.xserver.enable = true;

  # Enable the GNOME Desktop Environment.
  services.xserver.displayManager.gdm.enable = true;
  services.desktopManager.gnome.enable = true;
  environment.gnome.excludePackages = [ pkgs.epiphany ];

  # Configure keymap in X11
  services.xserver.xkb = {
    layout = "us";
    variant = "";
  };

  # Enable CUPS to print documents.
  services.printing.enable = true;

  # Enable sound with pipewire.
  services.pulseaudio.enable = false;
  security.rtkit.enable = true;
  services.pipewire = {
    enable = true;
    alsa.enable = true;
    alsa.support32Bit = true;
    pulse.enable = true;
    # If you want to use JACK applications, uncomment this
    #jack.enable = true;

    # use the example session manager (no others are packaged yet so this is enabled by default,
    # no need to redefine it in your config for now)
    #media-session.enable = true;
  };

  # Enable touchpad support (enabled default in most desktopManager).
  # services.xserver.libinput.enable = true;

  # Define a user account. Don't forget to set a password with ‘passwd’.
  users.users."m1y" = {
    isNormalUser = true;
    description = "Makariy";
    shell = pkgs.fish;
    extraGroups = [ "networkmanager" "wheel" ];
    packages = with pkgs; [
    #  thunderbird
    ];
  };

  # Install firefox.
  programs.firefox.enable = true;

  # Default web browser = Firefox
  xdg.mime.defaultApplications = {
    "text/html" = [ "firefox.desktop" ];
    "application/xhtml+xml" = [ "firefox.desktop" ];
    "x-scheme-handler/http" = [ "firefox.desktop" ];
    "x-scheme-handler/https" = [ "firefox.desktop" ];
  };
  programs.kdeconnect.enable = true;

  # Match cursor size set in niri (niri only controls the compositor cursor;
  # GTK apps draw their own from these gsettings).
  programs.dconf = {
    enable = true;
    profiles.user.databases = [
      {
        settings = {
          "org/gnome/desktop/interface" = {
            cursor-size = lib.gvariant.mkInt32 12;
          };
        };
      }
    ];
  };

  # Aliases for all shells
  environment.shellAliases = {
    ls = "lsd";
    cat = "bat";
  };

  # Fish shell with zoxide (z), bat (cat) and lsd (ls)
  programs.fish = {
    enable = true;
    shellInit = ''
      set -U fish_greeting
      fastfetch --logo none --structure title,os,uptime
    '';
    shellAliases = {
      ls = "lsd";
      cat = "bat";
    };
  };
  programs.zoxide = {
    enable = true;
    enableFishIntegration = true;
    flags = [ "--cmd" "cd" ];
  };

  # Allow unfree packages
  nixpkgs.config.allowUnfree = true;

  # List packages installed in system profile. To search, run:
  # $ nix search wget
  ##environment.systemPackages = with pkgs; [
  #  vim # Do not forget to add an editor to edit configuration.nix! The Nano editor is also installed by default.
  #  wget
  ##];

  # Some programs need SUID wrappers, can be configured further or are
  # started in user sessions.
  # programs.mtr.enable = true;
  # programs.gnupg.agent = {
  #   enable = true;
  #   enableSSHSupport = true;
  # };

  # List services that you want to enable:

  # Enable the OpenSSH daemon.
  # services.openssh.enable = true;

  # Open ports in the firewall.
  # networking.firewall.allowedTCPPorts = [ ... ];
  # networking.firewall.allowedUDPPorts = [ ... ];
  # Or disable the firewall altogether.
  # networking.firewall.enable = false;

  # This value determines the NixOS release from which the default
  # settings for stateful data, like file locations and database versions
  # on your system were taken. It‘s perfectly fine and recommended to leave
  # this value at the release version of the first install of this system.
  # Before changing this value read the documentation for this option
  # (e.g. man configuration.nix or on https://nixos.org/nixos/options.html).
  system.stateVersion = "26.05"; # Did you read the comment?

       nix.settings.experimental-features = [ "nix-command" "flakes" ];

environment.systemPackages = with pkgs; [
       # Browsers & messengers
          firefox
          discord
          telegram-desktop

       # Editors & IDEs
          vscode.fhs
          neovim
          opencode
          antigravity-cli
          androidStudioPackages.stable

       # Office (en-US, ru, lt only)
          (
            libreoffice-qt.override {
              unwrapped = libreoffice-qt-unwrapped.override {
                langs = [ "en-GB" "ru" "lt" ];
              };
            }
          )

       # Terminals & shell tooling
          alacritty
          git
          zoxide
          bat
          lsd
          fastfetch

       # Media
          spotify

       # Remote desktop
          rustdesk

       # Languages & toolchains
          python3
          gcc
          clang
          gdb
          ghc
          cabal-install
          stack
          haskell-language-server

       # Fonts
          (nerd-fonts.symbols-only)
          (nerd-fonts.jetbrains-mono)

       # Custom packages
          self.packages.${pkgs.stdenv.hostPlatform.system}.noctalia-shell
          eduvpn-client
       ];

     # Symlink configs into the user home
     systemd.tmpfiles.rules = [
       "L+ /home/m1y/.config/alacritty/alacritty.toml - - - - ${./alacritty.toml}"
       "d /home/m1y/.config/nvim 0700 m1y users -"
       "L+ /home/m1y/.config/nvim/init.lua - - - - ${./nvim-init.lua}"
       "L+ /home/m1y/.config/opencode/tui.json - - - - ${./opencode-tui.json}"
     ];
   };

}
