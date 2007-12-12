%define		apxs		/usr/sbin/apxs1
%define		mod_name	jserv
%include	/usr/lib/rpm/macros.java
Summary:	Servlet engine with support for the leading web server
Summary(pl.UTF-8):	Silnik serwletów ze wsparciem dla wiodącego serwera WWW
Name:		ApacheJServ
Version:	1.1.2
Release:	6
License:	freely distributable & usable
Group:		Networking/Daemons
Source0:	http://java.apache.org/jserv/dist/%{name}-%{version}.tar.gz
# Source0-md5:	6d48a1b9fcc5eea4dfebaae29ba5a485
Source2:	%{name}.conf
Source3:	%{name}.init
Source4:	%{name}.sysconfig
Source5:	runjserv
Patch0:		%{name}-enable-secret.patch
Patch1:		%{name}-ac.patch
Patch2:		%{name}-jre-env.patch
Patch3:		%{name}-config.patch
URL:		http://archive.apache.org/dist/java/jserv/
BuildRequires:	apache1-devel >= 1.3.9-8
BuildRequires:	autoconf
BuildRequires:	automake
BuildRequires:	gettext-devel
BuildRequires:	jdk
BuildRequires:	jpackage-utils
BuildRequires:	rpm-javaprov
BuildRequires:	rpmbuild(macros) >= 1.300
BuildRequires:	sed >= 4.0
BuildRequires:	servlet = 2.0
Requires(post,preun):	rc-scripts
Requires(pre):	/bin/id
Requires(pre):	/usr/bin/getgid
Requires(pre):	/usr/sbin/groupadd
Requires(pre):	/usr/sbin/useradd
Requires:	jpackage-utils
Requires:	jre
Requires:	rc-scripts >= 0.4.0.19
Requires:	servlet = 2.0
Provides:	group(jserv)
Provides:	user(jserv)
Obsoletes:	ApacheJServ-doc
Obsoletes:	ApacheJServ-init
Obsoletes:	jserv
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		_pkglibdir	%(%{apxs} -q LIBEXECDIR 2>/dev/null)
%define		httpdconf	%(%{apxs} -q SYSCONFDIR 2>/dev/null)
%define		_sysconfdir	/etc/jserv

%description
Apache JServ is a servlet engine, developed by the Java Apache Project
<http://java.apache.org/>. The Apache JServ servlet engine is written
in 100pc Java application, and listens for servlet requests using the
Apache Java protocol (AJp). Typically, these requests will originate
from the mod_jserv Apache module (DSO included).

%description -l pl.UTF-8
Apache JServ jest silnikiem serwletowym, rozwijanym przez Java Apache
Project <http://java.apache.org/>. Silnik serwletowy Apache JServ
został napisany od początku do końca w Javie; nasłuchuje wywołań
serwletu wykorzystując protokół Apache Java (AJp). Zazwyczaj wywołania
te pochodzą z modułu Apache mod_jservmodule (łącznie z DSO).

%package -n apache1-mod_jserv
Summary:	JServ module for Apache
Summary(pl.UTF-8):	Moduł JServ dla Apache'a
Group:		Networking/Daemons
Requires:	apache1-base >= 1.3.33-2
Obsoletes:	ApacheJServ-auto

%description -n apache1-mod_jserv
JServ module for Apache.

%description -n apache1-mod_jserv -l pl.UTF-8
Moduł JServ dla Apache'a.

%prep
%setup -q
%patch0 -p0
%patch1 -p0
%patch2 -p1
%patch3 -p1

# servlet-2.0 is the highest version the jserv code compiles with
servlet_jar=$(find-jar servlet-2.0)
%{__sed} -i -e "
	s|@JSDK_CLASSES@|$servlet_jar)|g
	s|@JAVA@|%java|g
" conf/jserv.properties.in

# do not load module in provided jserv.conf; we do this in httpd.conf
%{__sed} -i -e 's|@LOAD_OR_NOT@|#|g' conf/jserv.conf.in

# we don't want gcj related deps
%{__sed} -i -e '/^SUBDIRS/s,java,,' src/Makefile.am
%{__sed} -i -e '/^SUBDIRS/s,example,,' Makefile.am

%build
export JAVA_HOME="%{java_home}"
if [ ! -f _autotools.stamp ]; then
	%{__gettextize}
	%{__libtoolize}
	%{__aclocal}
	%{__autoconf}
	%{__automake}
	touch _autotools.stamp
fi

### JSERV
CFLAGS="$(%{apxs} -q CFLAGS) %{rpmcflags}"
dir=$(pwd)
%configure \
	%{!?debug:--disable-debugging} \
	--with-apxs=%{apxs} \
	--with-logdir=/var/log/jserv \
	--with-servlets=%{_datadir}/jserv/servlets \
	--with-java-platform=1.4 \
	--with-JSDK=$(find-jar servlet-2.0) \
	%{!?with_gcj:GCJ=javac GCJFLAGS= CLASSPATH=$dir JAVAC_OPT="-source 1.4"} \
	%{!?with_gcj:--with-javac=%{javac} --with-java=%{java} --with-jdk-home=$JAVA_HOME} \
	%{?with_gcj:--with-javac=%{_bindir}/gcj --with-jar=%{_bindir}/fastjar} \

%{__make} %{!?with_gcj:OBJEXT=class JAVAC_OPT='-source 1.4'} \
	-C src/java
%{__make}

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{/etc/{sysconfig,rc.d/init.d},%{httpdconf}/conf.d,%{_javadir},%{_sbindir}}

install %{SOURCE2} $RPM_BUILD_ROOT%{httpdconf}/conf.d/80_mod_jserv.conf
install %{SOURCE3} $RPM_BUILD_ROOT/etc/rc.d/init.d/jserv
install %{SOURCE4} $RPM_BUILD_ROOT/etc/sysconfig/jserv
install %{SOURCE5} $RPM_BUILD_ROOT%{_sbindir}

%{__make} install \
	DESTDIR=$RPM_BUILD_ROOT

# we removed java from SUBDIRS, so do it manually
%{__make} install \
	%{!?with_gcj:OBJEXT=class JAVAC_OPT='-source 1.4'} \
	-C src/java \
	DESTDIR=$RPM_BUILD_ROOT

> $RPM_BUILD_ROOT%{httpdconf}/jserv.secret.key
> $RPM_BUILD_ROOT%{_sysconfdir}/jserv.secret.key

install -d $RPM_BUILD_ROOT%{_datadir}/jserv/servlets

# duplicate
rm -f $RPM_BUILD_ROOT%{_sysconfdir}/jserv.conf
rm -rf $RPM_BUILD_ROOT%{_prefix}/docs

%clean
rm -rf $RPM_BUILD_ROOT

%pre
%groupadd -g 154 jserv
%useradd -u 154 -g jserv -d /etc/jserv -c "JServ User" jserv

%post
if [ ! -s %{_sysconfdir}/jserv.secret.key ]; then
	if [ -s %{httpdconf}/jserv.secret.key ]; then
		cat %{httpdconf}/jserv.secret.key > %{_sysconfdir}/jserv.secret.key
	else
		dd if=/dev/urandom bs=1 count=42 2>/dev/null \
			| (md5sum 2>/dev/null || cat) > %{_sysconfdir}/jserv.secret.key
	fi
fi
/sbin/chkconfig --add jserv
%service jserv restart "Apache JServ Daemon"

%preun
if [ "$1" = 0 ]; then
	%service jserv stop
	/sbin/chkconfig --del jserv
fi

%postun
if [ "$1" = "0" ]; then
	%userremove jserv
	%groupremove jserv
fi

%post -n apache1-mod_jserv
if [ ! -s %{httpdconf}/jserv.secret.key ]; then
	if [ -s %{_sysconfdir}/jserv.secret.key ]; then
		cat %{_sysconfdir}/jserv.secret.key > %{httpdconf}/jserv.secret.key
	else
		dd if=/dev/urandom bs=1 count=42 2>/dev/null \
			| (md5sum 2>/dev/null || cat) > %{httpdconf}/jserv.secret.key
	fi
fi
%service -q apache restart

%postun -n apache1-mod_jserv
if [ "$1" = "0" ]; then
	%service -q apache restart
fi

%files
%defattr(644,root,root,755)
%doc LICENSE README
%doc index.html docs
%dir %attr(750,root,jserv) %{_sysconfdir}
%attr(640,root,jserv) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/jserv.secret.key
%attr(640,root,jserv) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/jserv.properties
%attr(640,root,jserv) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/zone.properties
%attr(754,root,root) /etc/rc.d/init.d/jserv
%attr(755,root,root) %{_sbindir}/runjserv
%config(noreplace) %verify(not md5 mtime size) /etc/sysconfig/jserv
%{_javadir}/ApacheJServ.jar
%dir %{_datadir}/jserv
%dir %attr(750,root,jserv) %{_datadir}/jserv/servlets
%attr(770,root,jserv) %dir /var/log/jserv

%files -n apache1-mod_jserv
%defattr(644,root,root,755)
%attr(755,root,root) %{_pkglibdir}/mod_jserv.so
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) %{httpdconf}/conf.d/80_mod_jserv.conf
%attr(640,root,http) %config(noreplace) %verify(not md5 mtime size) %{httpdconf}/jserv.secret.key
