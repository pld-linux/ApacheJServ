# Conditional build:
%bcond_with	gcj	# use javac instead of GCJ

%define		jsdkversion	20000924
%define		apxs		/usr/sbin/apxs1
Summary:	Servlet engine with support for the leading web server
Summary(pl):	Silnik serwlet�w ze wsparciem dla wiod�cego serwera WWW
Name:		ApacheJServ
Version:	1.1.2
Release:	0.4
License:	freely distributable & usable (JServ), LGPL (JSDK)
Group:		Networking/Daemons
Source0:	http://java.apache.org/jserv/dist/%{name}-%{version}.tar.gz
# Source0-md5:	6d48a1b9fcc5eea4dfebaae29ba5a485
Source1:	http://www.euronet.nl/~pauls/java/servlet/download/classpathx_servlet-%{jsdkversion}.tar.gz
# Source1-md5:	a81feddb91b1358f9aaed94e83eddb54
Patch0:		%{name}-enable-secret.patch
Patch1:		%{name}-ac.patch
URL:		http://java.apache.org/
BuildRequires:	apache1-devel >= 1.3.9-8
%if %{with gcj}
BuildRequires:	gcc-java
BuildRequires:	fastjar
#BuildRequires:	gcc-java-tools
Requires:	/usr/bin/gij
%else
#BuildRequires:	jar
BuildRequires:	jdk
#Requires:	jre
%endif
Requires(post):	awk
Requires(post):	ed
Requires(post):	grep
Requires(post):	sh-utils
Requires(post):	textutils
Requires(post,preun):	fileutils
Requires(post,preun):	sed
Requires:	apache1 >= 1.3.6
Provides:	jserv
Provides:	jsdk20
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		libexecdir	%(%{apxs} -q LIBEXECDIR)
%define		httpdconf	%(%{apxs} -q SYSCONFDIR)
%define		jservconf	%{httpdconf}/jserv
%define		logdir		/var/log/httpd
%define		servletdir	%{_datadir}/jserv/servlets
%define		classesdir	%{_datadir}/jserv/classes
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
zosta� napisany od pocz�tku do ko�ca w Javie; nas�uchuje wywo�a�
serwletu wykorzystuj�c protok� Apache Java (AJp). Zazwyczaj wywo�ania
te pochodz� z modu�u Apache mod_jservmodule (��cznie z DSO). Pakiet
ten zawiera sunowsk� implementacj� api serlet�w w javie w wersji 2.0
(na licencji LGPL) napisana przez Paula Siegmanna
<http://www.euronet.nl/~pauls/java/servlet/>

%package doc
Summary:	ApacheJServ documentation
Group:		Development/Languages/Java

%description doc
ApacheJserv documentation.

%prep
%setup -q -a1
%patch0 -p0
%patch1 -p0

# final position of GNU JSDK-Classes
sed -i -e 's|@JSDK_CLASSES@|%{classesdir}/servlet-2.0.jar|g' conf/jserv.properties.in 

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

#%{!?with_gcj:GCJ=javac GCJFLAGS= CLASSPATH=`pwd`  JAVAC_OPT="-source 1.4" ac_cv_objext=class} \

### JSERV
APXS_CFLAGS=`%{apxs} -q CFLAGS`
%{!?with_gcj:GCJ=javac GCJFLAGS= CLASSPATH=`pwd`  JAVAC_OPT="-source 1.4"} \
CFLAGS="$APXS_CFLAGS %{rpmcflags}" ./configure \
	--prefix=%{_prefix} \
	--disable-debugging \
	--with-apxs=%{apxs} \
	--with-logdir=%{logdir} \
	--with-servlets=%{servletdir} \
    %{!?with_gcj:--with-javac=%{_bindir}/javac --with-jdk-home=%{_libdir}/java} \
    %{?with_gcj:--with-javac=%{_bindir}/gcj --with-jar=%{_bindir}/fastjar} \
	--with-JSDK=`pwd`/classpathx_servlet-%{jsdkversion}/servlet-2.0.jar \

%{__make} %{!?with_gcj:OBJEXT=class JAVAC_OPT='-source 1.4'} \
	-C src/java
%{__make}

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT%{classesdir}
#install -d $RPM_BUILD_ROOT/etc/{rc.d/init.d,profile.d,logrotate.d}

%{__make} install \
	DESTDIR=$RPM_BUILD_ROOT

# we removed java, so do it manually
%{__make} install \
	%{!?with_gcj:OBJEXT=class JAVAC_OPT='-source 1.4'} \
	-C src/java \
	DESTDIR=$RPM_BUILD_ROOT

echo "default - change on install `date`" > $RPM_BUILD_ROOT%{jservconf}/jserv.secret.key
chmod 600 $RPM_BUILD_ROOT%{jservconf}/jserv.secret.key

# currently disabled
#install -m755 src/scripts/package/rpm/jserv.init      $RPM_BUILD_ROOT/etc/rc.d/init.d/jserv
#install -m755 src/scripts/package/rpm/jserv.sh        $RPM_BUILD_ROOT/etc/profile.d
#install -m644 src/scripts/package/rpm/jserv.logrotate $RPM_BUILD_ROOT/etc/logrotate.d/jserv

### GNU JSDK-classes
install classpathx_servlet-%{jsdkversion}/servlet-2.0.jar $RPM_BUILD_ROOT%{classesdir}

find jsdk-doc -name 'Makefile*' | xargs rm -f
rm -rf jsdk-doc/{COPYING.LIB,CVS} jsdk-doc/apidoc/CVS

%clean
rm -rf $RPM_BUILD_ROOT

%post
# use fortune + install-date + process-list to create pseudo-random, hardly
# guessable secret key. Use md5sum to create a hash from this, if available:
(fortune 2>/dev/null ; date ; ps -eal 2>/dev/null) \
	| (md5sum 2>/dev/null || cat) > %{jservconf}/jserv.secret.key
chmod 600 %{jservconf}/jserv.secret.key

#
# determine apache-USER and chown the jserv.secrect.key - file
#
APACHEUSER=`grep "^User[	 ]\+" %{httpdconf}/httpd.conf | awk '{print $2}'`
if test ! "x$APACHEUSER" = x ; then
	USERCOMMENT="(which is '$APACHEUSER' ?)"
else
# assumption:
	APACHEUSER=http
fi
chown $APACHEUSER %{jservconf}/jserv.secret.key

#
# determine apache-GROUP and allow this group to write to %{logdir}
APACHEGROUP=`grep "^Group[	 ]\+" %{httpdconf}/httpd.conf | awk '{print $2}'`
if test "x$APACHEGROUP" = x ; then
	APACHEGROUP=http
fi
chgrp $APACHEGROUP %{logdir}
chmod g+w %{logdir}

#
# Add 'jserv' as an independent service (manual mode)
#/sbin/chkconfig --add jserv
#/etc/rc.d/init.d/jserv start

#
# Find Include Statement or add it if necessary
#
umask 027
cp -f %{httpdconf}/httpd.conf %{httpdconf}/httpd.conf.rpmorig
grep -q '#\?.*[iI]nclude.*/jserv.conf' %{httpdconf}/httpd.conf
if test $? -eq 0 ; then
	# found. Insert our include statement here
	## this depends on GNU-sed ('|')
	sed 's|^#\?\(.*Include\).*/jserv.conf.*$|\1 %{jservconf}/jserv.conf|g' \
		%{httpdconf}/httpd.conf.rpmorig > %{httpdconf}/httpd.conf
else
	# append it
	(
		echo "<IfModule mod_jserv.c>"
		echo "		Include %{jservconf}/jserv.conf"
		echo "</IfModule>"
	) >> %{httpdconf}/httpd.conf
fi

#
# LoadModule; uncomment or insert
#
grep -q '#\?.*LoadModule.*jserv_module.*mod_jserv.so' %{httpdconf}/httpd.conf
if test $? -eq 0 ; then
	# found. Remove any comment
	sed 's|^#.*\(LoadModule.*mod_jserv.so\)|\1|g' \
		%{httpdconf}/httpd.conf > %{httpdconf}/httpd.conf.loadMod
	mv -f %{httpdconf}/httpd.conf.loadMod %{httpdconf}/httpd.conf
else
	# Insert LoadModule line before first valid LoadModule
	(
		echo "/^LoadModule"
		echo "i"
		echo "LoadModule jserv_module	modules/mod_jserv.so"
		echo "."
		echo "wq"
	) | ed %{httpdconf}/httpd.conf > /dev/null 2>&1
fi

#
# AddModule; uncomment or insert
#
grep -q '#\?.*AddModule.*mod_jserv.c' %{httpdconf}/httpd.conf
if test $? -eq 0 ; then
	# found. Remove any comment
	sed 's|^#.*\(AddModule.*mod_jserv.c\)|\1|g' \
		%{httpdconf}/httpd.conf > %{httpdconf}/httpd.conf.addMod
	mv -f %{httpdconf}/httpd.conf.addMod %{httpdconf}/httpd.conf
else
	(
		echo "/^AddModule"
		echo "i"
		echo "AddModule mod_jserv.c"
		echo "."
		echo "wq"
	) | ed %{httpdconf}/httpd.conf > /dev/null 2>&1
fi

#
# Search for JAVA at possible locations and edit wrapper.bin
#
unset JAVABIN
for lookfor in java jre ; do
	for loc in \
		$JAVA_HOME \
		$JDK_HOME \
		%{_libdir}/java \
		/usr/local/java* \
		/usr/local/jdk*
	do
		if test -x "$loc/bin/$lookfor" ; then
			JAVABIN="$loc/bin/$lookfor"
			break
		fi
	done

	if test -z "$JAVABIN" ; then
		for prefix in /usr/jdk /usr/jdk- /usr/local/jdk /usr/local/jdk- ; do
			for jplatform in 2 1 ; do
				for subvers in .9 .8 .7 .6 .5 .4 .3 .2 .1 "" ; do
					if test -x "${prefix}1.$jplatform$subvers/bin/$lookfor" ; then
						JAVABIN="${prefix}1.$jplatform$subvers/bin/$lookfor"
						break
					fi
				done
				if test ! -z "$JAVABIN" ; then break ; fi
			done
			if test ! -z "$JAVABIN" ; then break ; fi
		done
	fi
	if test ! -z "$JAVABIN" ; then break ; fi
done

umask 022
if test ! -z "$JAVABIN" ; then
	sed "s|^wrapper.bin=.*$|wrapper.bin=$JAVABIN|" \
		%{jservconf}/jserv.properties > %{jservconf}/jserv.properties.new
	mv -f %{jservconf}/jserv.properties.new %{jservconf}/jserv.properties
fi

#
# Get Server Port to echo right URL below
#
SERVERPORT=`grep "^Port" %{httpdconf}/httpd.conf | \
			head -n 1 | awk '{print ":" $2}'`
if test "$SERVERPORT" = ":80" ; then
	SERVERPORT=""
fi

#FIXME:		make this i18n-aware

if test ! "x$JAVABIN" = x ; then
	echo "using java VM $JAVABIN"
else
	echo "## didn't find java or jre. Please install it and edit the"
	echo "## wrapper.bin property in %{jservconf}/jserv.properties"
fi
echo ""
echo "In order to enable JServ, restart the webserver and try"
echo "		 http://localhost$SERVERPORT/servlets/IsItWorking"
echo "	 and"
echo "		 http://localhost$SERVERPORT/jserv/"
echo "-- ENJOY! --"
echo ""

## we hopefully may distribute SUN-jsdk.jar with jserv once ..
echo " | NOTE that this distribution contains a fully functional"
echo " | free jsdk replacement, see <http://www.euronet.nl/~pauls/java/servlet/>."
echo " | If you want to use the SUN-jsdk, replace the servlet-2.0.jar"
echo " | in the wrapper.classpath - line in the file"
echo " |		 %{jservconf}/jserv.properties"
echo " | with the SUN jsdk."
echo " | Get it from <http://java.sun.com/products/servlet/>."
echo " | Only JSDK 2.0 (Java Servlet Development Kit)"
echo " | is supported (_EXACTLY_ 2.0)."
echo ""

echo "Please send comments/suggestions regarding"
echo "this RPM to <zeller@to.com>."

%preun
# do not remove the configured stuff if we upgrade.
# the $1 argument contains the number of packages _after_ installation.
if [ "$1" != "0" ] ; then
	exit 0
fi

# Remove 'jserv' service (manual mode)
#/etc/rc.d/init.d/jserv stop
#/sbin/chkconfig --del jserv

#
# Find jserv related configuration settings and comment
# them out
#
umask 027
cp -f %{httpdconf}/httpd.conf %{httpdconf}/httpd.conf.rpmorig
sed 's|.*\(Include.*%{jservconf}/jserv.conf\)|#\1|g' \
	%{httpdconf}/httpd.conf.rpmorig \
	| sed 's|^\(AddModule.*mod_jserv.c\)|#\1|g' \
	| sed 's|^\(LoadModule.*mod_jserv.so\)|#\1|g' \
	> %{httpdconf}/httpd.conf
# remove old logs
/bin/rm -fr %{logdir}/mod_jserv.log
/bin/rm -fr %{logdir}/jserv.log

%files
%defattr(644,root,root,755)
# mmh, we can't give %{_prefix}/docs to %doc ..
%doc LICENSE README

%dir %{jservconf}
%config(noreplace) %verify(not md5 mtime size) %{jservconf}/jserv.properties
%config(noreplace) %verify(not md5 mtime size) %{jservconf}/zone.properties
%config(noreplace) %verify(not md5 mtime size) %{jservconf}/jserv.conf

# these are just for demonstration and thus,
# no %config-files per-se; do not install
# them for the RPM-packet
#%%{jservconf}/jserv.properties.default
#%%{jservconf}/zone.properties.default
#%%{jservconf}/jserv.conf.default

%attr(600,http,http) %{jservconf}/jserv.secret.key
#%config /etc/rc.d/init.d/jserv
#%attr(640,root,root) %config(noreplace) %verify(not size mtime md5) /etc/logrotate.d/jserv
#%config /etc/profile.d/jserv.sh

%attr(755,root,root) %{libexecdir}/mod_jserv.so
%{libexecdir}/ApacheJServ.jar

%dir %{classesdir}
%{classesdir}/servlet-2.0.jar

%if 0
%dir %{servletdir}
%{servletdir}/Hello.java
%{servletdir}/Hello.class
%{servletdir}/IsItWorking.java
%{servletdir}/IsItWorking.class
%endif

# we need to have write access here
%attr(770,root,http) %dir %{logdir}

%files doc
%doc index.html docs
%doc jsdk-doc
