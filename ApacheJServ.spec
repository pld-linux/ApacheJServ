# TODO
# - separate package for jsdk?
#
# Conditional build:
%bcond_with	gcj	# use GCJ instead of javac
#
%define		apxs		/usr/sbin/apxs1
%define		jsdkversion	20000924
%define		mod_name	jserv
Summary:	Servlet engine with support for the leading web server
Summary(pl):	Silnik serwletów ze wsparciem dla wiod±cego serwera WWW
Name:		ApacheJServ
Version:	1.1.2
Release:	3
License:	freely distributable & usable (JServ), LGPL (JSDK)
Group:		Networking/Daemons
Source0:	http://java.apache.org/jserv/dist/%{name}-%{version}.tar.gz
# Source0-md5:	6d48a1b9fcc5eea4dfebaae29ba5a485
Source1:	http://www.euronet.nl/~pauls/java/servlet/download/classpathx_servlet-%{jsdkversion}.tar.gz
# Source1-md5:	a81feddb91b1358f9aaed94e83eddb54
Source2:	%{name}.conf
Source3:	%{name}.init
Source4:	%{name}.sysconfig
Source5:	runjserv
Patch0:		%{name}-enable-secret.patch
Patch1:		%{name}-ac.patch
Patch2:		%{name}-jre-env.patch
Patch3:		%{name}-config.patch
URL:		http://java.apache.org/
BuildRequires:	apache1-devel >= 1.3.9-8
BuildRequires:	autoconf
BuildRequires:	automake
BuildRequires:	gettext-devel
BuildRequires:	rpmbuild(macros) >= 1.268
BuildRequires:	sed >= 4.0
%if %{with gcj}
BuildRequires:	fastjar
BuildRequires:	gcc-java
BuildRequires:	jdkgcj
Requires:	/usr/bin/gij
%else
BuildRequires:	java-sun
Requires:	java-sun-jre
%endif
Requires(post,preun):	rc-scripts
Requires(pre):	/bin/id
Requires(pre):	/usr/bin/getgid
Requires(pre):	/usr/sbin/groupadd
Requires(pre):	/usr/sbin/useradd
Requires:	%{name} = %{version}-%{release}
Requires:	rc-scripts >= 0.4.0.19
Provides:	group(jserv)
Provides:	jsdk20
Provides:	jserv
Provides:	user(jserv)
Obsoletes:	ApacheJServ-init
Obsoletes:	jserv
ExclusiveArch:	i586 i686 pentium3 pentium4 athlon %{x8664}
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		_pkglibdir	%(%{apxs} -q LIBEXECDIR 2>/dev/null)
%define		httpdconf	%(%{apxs} -q SYSCONFDIR 2>/dev/null)
%define		_sysconfdir	/etc/jserv
%define		logdir		/var/log/jserv
%define		_noautocompressdoc  package-list

%description
Apache JServ is a servlet engine, developed by the Java Apache Project
<http://java.apache.org/>. The Apache JServ servlet engine is written
in 100pc Java application, and listens for servlet requests using the
Apache Java protocol (AJp). Typically, these requests will originate
from the mod_jserv Apache module (DSO included). This package contains
a LGPL'ed implementation of Sun's Java Servlet API version 2.0 by Paul
Siegmann <http://www.euronet.nl/~pauls/java/servlet/>.

%description -l pl
Apache JServ jest silnikiem serwletowym, rozwijanym przez Java Apache
Project <http://java.apache.org/>. Silnik serwletowy Apache JServ
zosta³ napisany od pocz±tku do koñca w Javie; nas³uchuje wywo³añ
serwletu wykorzystuj±c protokó³ Apache Java (AJp). Zazwyczaj wywo³ania
te pochodz± z modu³u Apache mod_jservmodule (³±cznie z DSO). Pakiet
ten zawiera implementacjê Java Servlet API Suna w wersji 2.0 napisan±
przez Paula Siegmanna (na licencji LGPL)
<http://www.euronet.nl/~pauls/java/servlet/>.

%package -n apache1-mod_jserv
Summary:	JServ module for Apache
Summary(pl):	Modu³ JServ dla Apache'a
Group:		Networking/Daemons
Requires:	apache1 >= 1.3.33-2
Obsoletes:	ApacheJServ-auto

%description -n apache1-mod_jserv
JServ module for Apache.

%description -n apache1-mod_jserv -l pl
Modu³ JServ dla Apache'a.

%package doc
Summary:	ApacheJServ documentation
Summary(pl):	Dokumentacja do ApacheJServ
Group:		Development/Languages/Java

%description doc
ApacheJserv documentation.

%description doc -l pl
Dokumentacja do ApacheJServ.

%prep
%setup -q -a1
%patch0 -p0
%patch1 -p0
%patch2 -p1
%patch3 -p1

sed -i -e '
	s|@JSDK_CLASSES@|%{_javadir}/servlet-2.0.jar|g
' conf/jserv.properties.in

# do not load module in provided jserv.conf; we do this in httpd.conf
sed -i -e 's|@LOAD_OR_NOT@|#|g' conf/jserv.conf.in

# we don't want gcj related deps
sed -i -e '/^SUBDIRS/s,java,,' src/Makefile.am
sed -i -e '/^SUBDIRS/s,example,,' Makefile.am

%build
export JAVA_HOME="%{java_home}"

if [ ! -f _autotools.done.1 ]; then
	%{__gettextize}
	%{__libtoolize}
	%{__aclocal}
	%{__autoconf}
	%{__automake}
	touch _autotools.done.1
fi

# prepare compilation
if [ ! -f classpathx_servlet-%{jsdkversion}/servlet-2.0.jar ]; then
	%{__make} -C classpathx_servlet-%{jsdkversion} jar_2_0
fi

if [ ! -d jsdk-doc ]; then
	%{__make} -C classpathx_servlet-%{jsdkversion}/apidoc

	# copy API-doc
	mkdir jsdk-doc
	cp classpathx_servlet-%{jsdkversion}/{README,AUTHORS,COPYING.LIB} jsdk-doc
	cp -r classpathx_servlet-%{jsdkversion}/apidoc jsdk-doc
fi

### JSERV
CFLAGS="$(%{apxs} -q CFLAGS) %{rpmcflags}"
dir=$(pwd)
%configure \
	%{!?debug:--disable-debugging} \
	--with-apxs=%{apxs} \
	--with-logdir=%{logdir} \
	--with-servlets=%{_datadir}/jserv/servlets \
	--with-java-platform=1.4 \
	--with-JSDK=$dir/classpathx_servlet-%{jsdkversion}/servlet-2.0.jar \
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

### GNU JSDK-classes
install classpathx_servlet-%{jsdkversion}/servlet-2.0.jar $RPM_BUILD_ROOT%{_javadir}

find jsdk-doc -name 'Makefile*' | xargs rm -f
rm -rf jsdk-doc/{COPYING.LIB,CVS} jsdk-doc/apidoc/CVS

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
%dir %attr(750,root,jserv) %{_sysconfdir}
%attr(640,root,jserv) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/jserv.secret.key
%attr(640,root,jserv) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/jserv.properties
%attr(640,root,jserv) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/zone.properties
%attr(754,root,root) /etc/rc.d/init.d/jserv
%attr(755,root,root) %{_sbindir}/runjserv
%config(noreplace) %verify(not md5 mtime size) /etc/sysconfig/jserv
%{_javadir}/ApacheJServ.jar
%{_javadir}/servlet-2.0.jar
%dir %{_datadir}/jserv
%dir %attr(750,root,jserv) %{_datadir}/jserv/servlets

%if 0
%{_datadir}/jserv/servlets/Hello.java
%{_datadir}/jserv/servlets/Hello.class
%{_datadir}/jserv/servlets/IsItWorking.java
%{_datadir}/jserv/servlets/IsItWorking.class
%endif
%attr(770,root,jserv) %dir %{logdir}

%files -n apache1-mod_jserv
%defattr(644,root,root,755)
%attr(755,root,root) %{_pkglibdir}/mod_jserv.so
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) %{httpdconf}/conf.d/80_mod_jserv.conf
%attr(640,root,http) %config(noreplace) %verify(not md5 mtime size) %{httpdconf}/jserv.secret.key

%files doc
%defattr(644,root,root,755)
%doc index.html docs
%doc jsdk-doc
