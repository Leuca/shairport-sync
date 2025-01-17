Name:           {{{ git_dir_name }}}-unstable
Version:        {{{ shairport_version }}}
Release:        {{{ shairport_release }}}%{?dist}
Summary:        AirTunes emulator. Multi-Room with Audio Synchronisation (unstable)
# MIT licensed except for tinysvcmdns under BSD, 
# FFTConvolver/ under GPLv3+ and audio_sndio.c 
# under ISC
License:        MIT and BSD and GPLv3+ and ISC
URL:            https://github.com/mikebrady/shairport-sync
Source:         {{{ git_dir_pack }}}

BuildRequires:  make
BuildRequires:  automake
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  git
BuildRequires:  autoconf
BuildRequires:  automake
BuildRequires:  avahi-devel
BuildRequires:  libconfig-devel
BuildRequires:  openssl-devel
BuildRequires:  popt-devel
BuildRequires:  soxr-devel
BuildRequires:  libplist-devel
BuildRequires:  libsodium-devel
BuildRequires:  libgcrypt-devel
BuildRequires:  libuuid-devel
BuildRequires:  libalac-devel
BuildRequires:  vim-common
BuildRequires:  alsa-lib-devel
BuildRequires:  systemd-rpm-macros
# Allow build with both free and non-free versions
BuildRequires:  (libavformat-devel or libavformat-free-devel)
BuildRequires:  (libavutil-devel or libavutil-free-devel)
BuildRequires:  (libavcodec-devel or libavcodec-free-devel)

Requires:       nqptp-unstable

%description
Shairport Sync emulates an AirPort Express for the purpose of streaming audio
from iTunes, iPods, iPhones, iPads and AppleTVs. Audio played by a Shairport
Sync-powered device stays synchronised with the source and hence with similar
devices playing the same source. Thus, for example, synchronised multi-room
audio is possible without difficulty. (Hence the name Shairport Sync, BTW.)

Shairport Sync does not support AirPlay video or photo streaming.

This version of Shairport Sync has been built from the development branch

%prep
{{{ git_dir_setup_macro }}}

%build
autoreconf -i -f
%configure --with-avahi --with-systemd --with-alsa --with-ssl=openssl --with-soxr --with-apple-alac --with-airplay-2 --without-create-user-group
%make_build

%install
%make_install
rm %{buildroot}/etc/shairport-sync.conf.sample

%pre
getent group %{name} &>/dev/null || groupadd -r %{name} &>/dev/null
getent passwd %{name} &>/dev/null || useradd -r -M -g %{name} \
        -s /sbin/nologin \
        -G audio %{name} &>/dev/null

%post
%systemd_post %{name}.service

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun_with_restart %{name}.service

%files
%config(noreplace) /etc/shairport-sync.conf
/usr/bin/shairport-sync
/usr/share/man/man1/shairport-sync.1.gz
%{_unitdir}/shairport-sync.service
%doc README.md RELEASENOTES.md TROUBLESHOOTING.md
%license LICENSES

%changelog
{{{ git_dir_changelog }}}
