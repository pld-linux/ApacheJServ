# Conditional build:
%bcond_with	gcj	# use javac instead of GCJ

%define		apxs		/usr/sbin/apxs1
%define		jsdkversion	20000924
Summary:	Servlet engine with support for the leading web server
Summary(pl):	Silnik serwletów ze wsparciem dla wiod±cego serwera WWW
Name:		ApacheJServ
Version:	1.1.2
Release:	0.19
License:	freely distributable & usable (JServ), LGPL (JSDK)
Group:		Networking/Daemons
Source0:	http://java.apache.org/jserv/dist/%{name}-%{version}.tar.gz
# Source0-md5:	6d48a1b9fcc5eea4dfebaae29ba5a485
Source1:	http://www.euronet.nl/~pauls/java/servlet/download/classpathx_servlet-%{jsdkversion}.tar.gz
# Source1-md5:	a81feddb91b1358f9aaed94e83eddb54
Source2:	%{name}.conf
Source3:	%{name}.init
Patch0:		%{name}-enable-secret.patch
Patch1:		%{name}-ac.patch
URL:		http://java.apache.org/
BuildRequires:	apache1-devel >= 1.3.9-8
BuildRequires:	rpmbuild(macros) >= 1.228
BuildRequires:	sed >= 4.0
%if %{with gcj}
BuildRequires:	gcc-java
BuildRequires:	fastjar
Requires:	/usr/bin/gij
%else
BuildRequires:	jdk
%endif
Requires(post,preun):	rc-scripts
Requires:	apache1 >= 1.3.33-2
Provides:	jserv
Provides:	jsdk20
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		_pkglibdir	%(%{apxs} -q LIBEXECDIR 2>/dev/null)
%define		x_sysconfdir	%(%{apxs} -q SYSCONFDIR 2>/dev/null)
%define		httpdconf	%(%{apxs} -q SYSCONFDIR 2>/dev/null)
%define		_sysconfdir	/etc/jserv
%define		x_sysconfdir	%{httpdconf}/jserv
%define		logdir		/var/log/jserv
%define		servletdir	%{_datadir}/jserv/servlets
%define		_noautocompressdoc  package-list

%description
Apache JServ is a servlet engine, developed by the Java Apache Project
<http://java.apache.org/>. The Apache JServ servlet engine is written
in 100pc Java application, and listens for servlet requests using the
Apache Java protocol (AJp). Typically, these requests will originate
from the mod_jserv Apache module (DSO included). This package contains
a LGPL'ed implementation of sun's java servlet api version 2.0 by Paul
Siegmann <http://www.euronet.nl/~pauls/java/servlet/>

%description -l pl
Apache JServ jest silnikiem serwletowym, rozwijanym przez Java Apache
Project <http://java.apache.org/>. Silnik serwletowy Apache JServ
zosta³ napisany od pocz±tku do koñca w Javie; nas³uchuje wywo³añ
serwletu wykorzystuj±c protokó³ Apache Java (AJp). Zazwyczaj wywo³ania
te pochodz± z modu³u Apache mod_jservmodule (³±cznie z DSO). Pakiet
ten zawiera sunowsk± implementacjê api serletów w javie w wersji 2.0
(na licencji LGPL) napisana przez Paula Siegmanna
<http://www.euronet.nl/~pauls/java/servlet/>

%package init
Summary:	ApacheJServ initscript
Group:		Development/Languages/Java
Requires:	%{name} = %{version}-%{release}

%description init
JServ initscript for standalone mode.

%package doc
Summary:	ApacheJServ documentation
Group:		Development/Languages/Java

%description doc
ApacheJserv documentation.

%prep
%setup -q -a1
%patch0 -p0
%patch1 -p0

sed -i -e '
	s|@JSDK_CLASSES@|%{_javadir}/servlet-2.0.jar|g
' conf/jserv.properties.in

# do not load module in provided jserv.conf; we do this in httpd.conf
sed -i -e 's|@LOAD_OR_NOT@|#|g' conf/jserv.conf.in

# we don't want gcj related deps
sed -i -e '/^SUBDIRS/s,java,,' src/Makefile.am
sed -i -e '/^SUBDIRS/s,example,,' Makefile.am

%build
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
%configure \
	%{!?debug:--disable-debugging} \
	--with-apxs=%{apxs} \
	--with-logdir=%{logdir} \
	--with-servlets=%{servletdir} \
	%{!?with_gcj:GCJ=javac GCJFLAGS= CLASSPATH=`pwd` JAVAC_OPT="-source 1.4"} \
    %{!?with_gcj:--with-javac=%{_bindir}/javac --with-jdk-home=%{_libdir}/java} \
    %{?with_gcj:--with-javac=%{_bindir}/gcj --with-jar=%{_bindir}/fastjar} \
	--with-JSDK=`pwd`/classpathx_servlet-%{jsdkversion}/servlet-2.0.jar

%{__make} %{!?with_gcj:OBJEXT=class JAVAC_OPT='-source 1.4'} \
	-C src/java
%{__make}

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT%{_javadir}
install -d $RPM_BUILD_ROOT/etc/apache/conf.d
install -d $RPM_BUILD_ROOT/etc/{rc.d/init.d,profile.d,logrotate.d}
install %{SOURCE2} $RPM_BUILD_ROOT/etc/apache/conf.d/81_mod_jserv.conf
install %{SOURCE3} $RPM_BUILD_ROOT/etc/rc.d/init.d/jserv

%{__make} install \
	DESTDIR=$RPM_BUILD_ROOT

# we removed java, so do it manually
%{__make} install \
	%{!?with_gcj:OBJEXT=class JAVAC_OPT='-source 1.4'} \
	-C src/java \
	DESTDIR=$RPM_BUILD_ROOT

echo "default - change on install `date`" > $RPM_BUILD_ROOT%{_sysconfdir}/jserv.secret.key

# currently disabled
#install src/scripts/package/rpm/jserv.init      $RPM_BUILD_ROOT/etc/rc.d/init.d/jserv
#install src/scripts/package/rpm/jserv.sh        $RPM_BUILD_ROOT/etc/profile.d
#install src/scripts/package/rpm/jserv.logrotate $RPM_BUILD_ROOT/etc/logrotate.d/jserv

### GNU JSDK-classes
install classpathx_servlet-%{jsdkversion}/servlet-2.0.jar $RPM_BUILD_ROOT%{_javadir}

find jsdk-doc -name 'Makefile*' | xargs rm -f
rm -rf jsdk-doc/{COPYING.LIB,CVS} jsdk-doc/apidoc/CVS

%clean
rm -rf $RPM_BUILD_ROOT

%post
if [ "$1" = 1 ]; then
	# use fortune + install-date + process-list to create pseudo-random, hardly
	# guessable secret key. Use md5sum to create a hash from this, if available:
	(fortune 2>/dev/null; date; ps -eal 2>/dev/null) \
		| (md5sum 2>/dev/null || cat) > %{_sysconfdir}/jserv.secret.key
fi
%service apache restart

%postun
if [ "$1" = "0" ]; then
	%service -q apache restart
fi

%post init
/sbin/chkconfig --add jserv

%preun init
if [ "$1" = 0 ]; then
	if [ -f /var/lock/subsys/jserv ]; then
		/etc/rc.d/init.d/jserv stop 1>&2
	fi
	/sbin/chkconfig --del jserv
fi

%files
%defattr(644,root,root,755)
%doc LICENSE README
%dir %{_sysconfdir}
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) %{httpdconf}/conf.d/*_mod_jserv.conf
%attr(640,root,http) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/jserv.properties
%attr(640,root,http) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/zone.properties
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/jserv.conf
%attr(640,root,http) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/jserv.secret.key
#%attr(640,root,root) %config(noreplace) %verify(not size mtime md5) /etc/logrotate.d/jserv
#%config /etc/profile.d/jserv.sh

%attr(755,root,root) %{_pkglibdir}/mod_jserv.so

%{_javadir}/ApacheJServ.jar
%{_javadir}/servlet-2.0.jar

%if 0
%dir %{servletdir}
%{servletdir}/Hello.java
%{servletdir}/Hello.class
%{servletdir}/IsItWorking.java
%{servletdir}/IsItWorking.class
%endif

%attr(770,root,http) %dir %{logdir}

%files init
%defattr(644,root,root,755)
%attr(754,root,root) /etc/rc.d/init.d/jserv

%files doc
%defattr(644,root,root,755)
%doc index.html docs
%doc jsdk-doc
