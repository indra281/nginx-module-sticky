#
%define nginx_user nginx
%define nginx_group nginx

# distribution specific definitions
%define use_systemd (0%{?rhel} >= 7 || 0%{?fedora} >= 19 || 0%{?suse_version} >= 1315 || 0%{?amzn} >= 2)

%if %{use_systemd}
BuildRequires: systemd
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd
%endif

%if 0%{?rhel} || 0%{?amzn}
%define _group System Environment/Daemons
BuildRequires: openssl-devel
%endif

%if 0%{?rhel} == 6
Requires(pre): shadow-utils
Requires: initscripts >= 8.36
Requires(post): chkconfig
Requires: openssl >= 1.0.1
BuildRequires: openssl-devel >= 1.0.1
%endif

%if 0%{?rhel} == 7
BuildRequires: redhat-lsb-core
%define epoch 1
Epoch: %{epoch}
%define os_minor %(lsb_release -rs | cut -d '.' -f 2)
%if %{os_minor} == 4
%define dist .el7_4
%else
%define dist .el7
%endif
%endif

%if 0%{?rhel} == 8
%define epoch 1
Epoch: %{epoch}
Requires(pre): shadow-utils
BuildRequires: openssl-devel >= 1.1.1
%define _debugsource_template %{nil}
%endif

%if 0%{?suse_version} >= 1315
%define _group Productivity/Networking/Web/Servers
BuildRequires: libopenssl-devel
%endif

BuildRequires: expat-devel
BuildRequires: git

%define base_version 1.18.0
%define base_release 2%{?dist}.ngx

%define bdir %{_builddir}/%{name}-%{base_version}

Summary: nginx sticky dynamic module
Name: nginx-module-sticky
Version: %{base_version}
Release: %{base_release}
Vendor: Nginx, Inc.
URL: http://nginx.org/
Group: %{_group}

Source0: http://nginx.org/download/nginx-%{base_version}.tar.gz

License: 2-clause BSD-like license

BuildRoot: %{_tmppath}/%{name}-%{base_version}-%{base_release}-root
BuildRequires: zlib-devel
BuildRequires: pcre-devel
Requires: nginx == %{?epoch:%{epoch}:}%{base_version}-%{base_release}

%description
nginx sticky dynamic module.

%if 0%{?suse_version} || 0%{?amzn}
%debug_package
%endif

%define WITH_CC_OPT $(echo %{optflags} $(pcre-config --cflags))
%define WITH_LD_OPT -Wl,-z,relro -Wl,-z,now

%define BASE_CONFIGURE_ARGS $(echo "--prefix=%{_sysconfdir}/nginx --sbin-path=%{_sbindir}/nginx --modules-path=%{_libdir}/nginx/modules --conf-path=%{_sysconfdir}/nginx/nginx.conf --error-log-path=%{_localstatedir}/log/nginx/error.log --http-log-path=%{_localstatedir}/log/nginx/access.log --pid-path=%{_localstatedir}/run/nginx.pid --lock-path=%{_localstatedir}/run/nginx.lock --http-client-body-temp-path=%{_localstatedir}/cache/nginx/client_temp --http-proxy-temp-path=%{_localstatedir}/cache/nginx/proxy_temp --http-fastcgi-temp-path=%{_localstatedir}/cache/nginx/fastcgi_temp --http-uwsgi-temp-path=%{_localstatedir}/cache/nginx/uwsgi_temp --http-scgi-temp-path=%{_localstatedir}/cache/nginx/scgi_temp --user=%{nginx_user} --group=%{nginx_group} --with-compat --with-file-aio --with-threads --with-http_addition_module --with-http_auth_request_module --with-http_dav_module --with-http_flv_module --with-http_gunzip_module --with-http_gzip_static_module --with-http_mp4_module --with-http_random_index_module --with-http_realip_module --with-http_secure_link_module --with-http_slice_module --with-http_ssl_module --with-http_stub_status_module --with-http_sub_module --with-http_v2_module --with-mail --with-mail_ssl_module --with-stream --with-stream_realip_module --with-stream_ssl_module --with-stream_ssl_preread_module")
%define MODULE_CONFIGURE_ARGS $(echo "--add-dynamic-module=%{bdir}/nginx-sticky-module-ng")

%prep
%setup -qcTn %{name}-%{base_version}
tar --strip-components=1 -zxf %{SOURCE0}
git clone https://bitbucket.org/nginx-goodies/nginx-sticky-module-ng.git
cat <<EOF > nginx-sticky-module-ng/config
# OVERWITE NEW STYLE CONFIG
# This file is base on https://bitbucket.org/nginx-goodies/nginx-sticky-module-ng/issues/25/converting-the-config-file-for-dynamic
ngx_addon_name=ngx_http_sticky_module
if test -n "\$ngx_module_link"; then
    ngx_module_type=HTTP
    ngx_module_name=ngx_http_sticky_module
    ngx_module_srcs="\$ngx_addon_dir/ngx_http_sticky_module.c \$ngx_addon_dir/ngx_http_sticky_misc.c"
    ngx_module_deps="\$ngx_addon_dir/ngx_http_sticky_misc.h"
    . auto/module
else
    HTTP_MODULES="\$HTTP_MODULES ngx_http_sticky_module"
    NGX_ADDON_SRCS="\$NGX_ADDON_SRCS \$ngx_addon_dir/ngx_http_sticky_module.c \$ngx_addon_dir/ngx_http_sticky_misc.c"
    NGX_ADDON_DEPS="\$NGX_ADDON_DEPS \$ngx_addon_dir/ngx_http_sticky_misc.h"
fi
EOF


%build

cd %{bdir}
./configure %{BASE_CONFIGURE_ARGS} %{MODULE_CONFIGURE_ARGS} \
	--with-cc-opt="%{WITH_CC_OPT}" \
	--with-ld-opt="%{WITH_LD_OPT}" \
	--with-debug
make %{?_smp_mflags} modules
for so in `find %{bdir}/objs/ -type f -name "*.so"`; do
debugso=`echo $so | sed -e "s|.so|-debug.so|"`
mv $so $debugso
done
./configure %{BASE_CONFIGURE_ARGS} %{MODULE_CONFIGURE_ARGS} \
	--with-cc-opt="%{WITH_CC_OPT}" \
	--with-ld-opt="%{WITH_LD_OPT}"
make %{?_smp_mflags} modules

%install
cd %{bdir}
%{__rm} -rf $RPM_BUILD_ROOT

%{__mkdir} -p $RPM_BUILD_ROOT%{_libdir}/nginx/modules
for so in `find %{bdir}/objs/ -maxdepth 1 -type f -name "*.so"`; do
%{__install} -m755 $so \
   $RPM_BUILD_ROOT%{_libdir}/nginx/modules/
done

%clean
%{__rm} -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%{_libdir}/nginx/modules/*


%post
if [ $1 -eq 1 ]; then
cat <<BANNER
----------------------------------------------------------------------

The sticky dynamic module for nginx has been installed.
To enable this module, add the following to /etc/nginx/nginx.conf
and reload nginx:

    load_module modules/ngx_http_sticky_module.so;

Please refer to the module documentation for further details:
https://bitbucket.org/nginx-goodies/nginx-sticky-module-ng/

----------------------------------------------------------------------
BANNER
fi

%changelog
* Wed Nov 25 2020 Shigechika AIKAWA
- sync w/ nginx-1.18.0-2 rpm.

* Fri May 22 2020 Shigechika AIKAWA
- sync w/ nginx-1.18.0.

* Thu Aug 22 2019 Shigechika AIKAWA
- sync w/ nginx-1.16.1

* Thu Jun 27 2019 Shigechika AIKAWA
- base version updated to 1.16.0

* Wed Dec 05 2018 Shigechika AIKAWA
- base version updated to 1.14.2

* Tue Nov 13 2018 Shigechika AIKAWA
- base version updated to nginx-1.14.1.

* Mon May 07 2018 Shigechika AIKAWA
- base version updated to nginx-1.14.0.

* Mon Oct 23 2017 Shigechika AIKAWA
- base on nginx-1.12.2
- referenced nginx module spec files.
