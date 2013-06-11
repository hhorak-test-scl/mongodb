%{?scl:%scl_package mongodb}
%global pkg_name mongodb

%global         daemon mongod

Name:           %{?scl_prefix}mongodb
Version:        2.2.3
Release:        6%{?dist}
Summary:        High-performance, schema-free document-oriented database
Group:          Applications/Databases
License:        AGPLv3 and zlib and ASL 2.0
# util/md5 is under the zlib license
# manpages and bson are under ASL 2.0
# everything else is AGPLv3
URL:            http://www.mongodb.org

Source0:        http://fastdl.mongodb.org/src/%{pkg_name}-src-r%{version}.tar.gz
Source2:        %{pkg_name}.logrotate
Source3:        %{pkg_name}.conf
Source4:        %{daemon}.sysconf
Source5:        %{pkg_name}-tmpfile
Source6:        %{daemon}.service
Patch1:         mongodb-2.2.0-no-term.patch
##Patch 5 - https://jira.mongodb.org/browse/SERVER-6686
Patch5:         mongodb-2.2.0-fix-xtime.patch
%if 0%{?el6} == 0
##Patch 6 - https://jira.mongodb.org/browse/SERVER-4314
Patch6:         mongodb-2.2.0-boost-filesystem3.patch
%endif
##Patch 7 - make it possible to use system libraries
Patch7:         mongodb-2.2.0-use-system-version.patch
##Patch 8 - make it possible to build shared libraries
Patch8:         mongodb-2.2.0-shared-library.patch
##Patch 9 - https://jira.mongodb.org/browse/SERVER-5575
Patch9:         mongodb-2.2.0-full-flag.patch
##Patch 10 - https://bugzilla.redhat.com/show_bug.cgi?id=927536
##Patch 10 - https://jira.mongodb.org/browse/SERVER-9124
Patch10:        mongodb-2.2.3-CVE-2013-1892-avoid-raw-pointers.patch
Patch11:	mongodb-debug.patch

BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:  python-devel
BuildRequires:  %{?scl_prefix}scons
BuildRequires:  openssl-devel
BuildRequires:  boost-devel
BuildRequires:  pcre-devel
BuildRequires:  %{?scl_prefix}v8-devel
BuildRequires:  readline-devel
BuildRequires:  libpcap-devel
BuildRequires:  %{?scl_prefix}snappy-devel
BuildRequires:  %{?scl_prefix}gperftools-devel
BuildRequires:  %{?scl_prefix}libunwind-devel

Requires(post): systemd-units
Requires(preun): systemd-units

Requires(pre):  shadow-utils

Requires(postun): systemd-units

Requires:       %{name}-lib = %{version}-%{release}

# Mongodb must run on a little-endian CPU (see bug #630898)
ExcludeArch:    ppc ppc64 %{sparc} s390 s390x

%{?scl:Requires:%scl_runtime}

%description
Mongo (from "humongous") is a high-performance, open source, schema-free
document-oriented database. MongoDB is written in C++ and offers the following
features:
    * Collection oriented storage: easy storage of object/JSON-style data
    * Dynamic queries
    * Full index support, including on inner objects and embedded arrays
    * Query profiling
    * Replication and fail-over support
    * Efficient storage of binary data including large objects (e.g. photos
    and videos)
    * Auto-sharding for cloud-level scalability (currently in early alpha)
    * Commercial Support Available

A key goal of MongoDB is to bridge the gap between key/value stores (which are
fast and highly scalable) and traditional RDBMS systems (which are deep in
functionality).

%package lib
Summary:        MongoDB shared libraries
Group:          Development/Libraries

%description lib
This package provides the shared library for the MongoDB client.

%package devel
Summary:        MongoDB header files
Group:          Development/Libraries
Requires:       %{name}-lib = %{version}-%{release}
Requires:       boost-devel

%description devel
This package provides the header files and C++ driver for MongoDB. MongoDB is
a high-performance, open source, schema-free document-oriented database.

%package server
Summary:        MongoDB server, sharding server and support scripts
Group:          Applications/Databases
Requires:       %{name} = %{version}-%{release}

%description server
This package provides the mongo server software, mongo sharding server
software, default configuration files, and init scripts.


%prep
%setup -q -n mongodb-src-r%{version}
%patch1 -p1
%patch5 -p1
%if 0%{?el6} == 0
%patch6 -p1
%endif
%patch7 -p1
%patch8 -p1
%ifarch %ix86
%patch9 -p1
%endif
%patch10 -p1

sed -e "s|__SCL_LIBDIR__|%{_libdir}|g" %PATCH11 | patch -p1 -b --suffix .debug

# copy source files, because we want adjust paths
cp %{SOURCE2} %{SOURCE3} %{SOURCE4} %{SOURCE5} %{SOURCE6} .

sed -i  -e "s|/var/log/mongodb/|/var/log/%{?scl_prefix}mongodb/|g" \
        -e "s|/var/run/mongodb/|%{?_scl_root}/var/run/mongodb/|g" \
	%{pkg_name}.logrotate

sed -i	-e 's|/var/lib/mongodb|%{?_scl_root}/var/lib/mongodb|g' \
	-e 's|/var/run/mongodb|%{?_scl_root}/var/run/mongodb|g' \
	-e 's|/var/log/mongodb|/var/log/%{?scl_prefix}mongodb|g' \
	%{pkg_name}.conf

sed -i	-e 's|/etc/mongodb.conf|%{_sysconfdir}/mongodb.conf|g' \
	%{daemon}.sysconf        

sed -i	-e 's|/run/mongodb|%{?_scl_root}/run/mongodb|g' \
	%{pkg_name}-tmpfile

sed -i	-e 's|/var/run/mongodb|%{?_scl_root}/var/run/mongodb|g' \
	-e 's|/etc/sysconfig/mongod|%{_sysconfdir}/sysconfig/mongod|g' \
	-e 's|/usr/bin/mongo|%{_bindir}/mongo|g' \
	-e 's|__SCL_SCRIPTS__|%{?_scl_scripts}|g' \
	%{daemon}.service

# spurious permissions
chmod -x README

# wrong end-of-file encoding
sed -i 's/\r//' README

%build
# NOTE: Build flags must be EXACTLY the same in the install step!
# If you fail to do this, mongodb will be built twice...
%{?scl:scl enable %{scl} - << "EOF"}
export SCONS_LIB_DIR=%{_libdir}
scons \
	%{?_smp_mflags} \
	--sharedclient \
	--prefix=%{buildroot}%{_prefix} \
	--extrapath=%{_prefix} \
	--extrapathdyn=%{_prefix} \
	--nostrip \
	--ssl \
	--usev8 \
	--use-system-all \
	--full
#	--use-system-pcre=USE-SYSTEM-PCRE \
#	--use-system-boost=USE-SYSTEM-BOOST \
#	--libpath=%{_libdir} \
#	--cpppath=%{_includedir} \

%{?scl:EOF}

%install
rm -rf %{buildroot}
# NOTE: Install flags must be EXACTLY the same in the build step!
# If you fail to do this, mongodb will be built twice...
%{?scl:scl enable %{scl} - << "EOF"}
export SCONS_LIB_DIR=%{_libdir}
scons install \
	%{?_smp_mflags} \
	--sharedclient \
	--prefix=%{buildroot}%{_prefix} \
	--extrapath=%{_prefix} \
	--extrapathdyn=%{_prefix} \
	--nostrip \
	--ssl \
	--usev8 \
	--use-system-all \
	--full
#	--use-system-pcre=USE-SYSTEM-PCRE \
#	--use-system-boost=USE-SYSTEM-BOOST \
#	--libpath=%{_libdir} \
#	--cpppath=%{_includedir} \

%{?scl:EOF}

rm -f %{buildroot}%{_libdir}/libmongoclient.a
rm -f %{buildroot}%{_prefix}/lib/libmongoclient.a

mkdir -p %{buildroot}%{?_scl_root}/var/lib/%{pkg_name}
mkdir -p %{buildroot}/var/log/%{?scl_prefix}%{pkg_name}
mkdir -p %{buildroot}%{?_scl_root}/var/run/%{pkg_name}
mkdir -p %{buildroot}%{_sysconfdir}/sysconfig

mkdir -p %{buildroot}/lib/systemd/system
install -p -D -m 644 %{pkg_name}-tmpfile %{buildroot}/usr/lib/tmpfiles.d/%{?scl_prefix}mongodb.conf
install -p -D -m 644 %{daemon}.service %{buildroot}/lib/systemd/system/%{?scl_prefix}%{daemon}.service
install -p -D -m 644 %{pkg_name}.logrotate %{buildroot}/etc/logrotate.d/%{?scl_prefix}%{name}
install -p -D -m 644 %{pkg_name}.conf %{buildroot}%{_sysconfdir}/mongodb.conf
install -p -D -m 644 %{daemon}.sysconf %{buildroot}%{_sysconfdir}/sysconfig/%{daemon}

mkdir -p %{buildroot}%{_mandir}/man1
cp -p debian/*.1 %{buildroot}%{_mandir}/man1/

mkdir -p %{buildroot}%{?_scl_root}/var/run/%{name}

# In mongodb 2.2.2 we have duplicate headers
#  Everything should be in %{_includedir}/mongo
#  but it is almost all duplicated in %{_includedir}
#  which could potentially conflict
#  or cause problems.
mkdir -p %{buildroot}/%{pkg_name}-hold
mv %{buildroot}/%{_includedir}/mongo %{buildroot}/%{pkg_name}-hold/mongo
rm -rf %{buildroot}/%{_includedir}/*
mv %{buildroot}/%{pkg_name}-hold/mongo %{buildroot}/%{_includedir}/mongo
rm -rf %{buildroot}/%{pkg_name}-hold

%clean
rm -rf %{buildroot}

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%pre server
getent group %{pkg_name} >/dev/null || groupadd -r %{pkg_name}
getent passwd %{pkg_name} >/dev/null || \
useradd -r -g %{pkg_name} -u 184 -d %{?_scl_root}/var/lib/%{pkg_name} -s /sbin/nologin \
-c "MongoDB Database Server" %{pkg_name}
exit 0

%post server
%systemd_post %{?scl_prefix}mongod.service


%preun server
%systemd_preun %{?scl_prefix}mongod.service


%postun server
%systemd_postun_with_restart %{?scl_prefix}mongod.service


%files
%defattr(-,root,root,-)
%{_bindir}/bsondump
%{_bindir}/mongo
%{_bindir}/mongodump
%{_bindir}/mongoexport
%{_bindir}/mongofiles
%{_bindir}/mongoimport
%{_bindir}/mongooplog
%{_bindir}/mongoperf
%{_bindir}/mongorestore
%{_bindir}/mongostat
%{_bindir}/mongosniff
%{_bindir}/mongotop

%{_mandir}/man1/mongo.1*
%{_mandir}/man1/mongodump.1*
%{_mandir}/man1/mongoexport.1*
%{_mandir}/man1/mongofiles.1*
%{_mandir}/man1/mongoimport.1*
%{_mandir}/man1/mongosniff.1*
%{_mandir}/man1/mongostat.1*
%{_mandir}/man1/mongorestore.1*
%{_mandir}/man1/bsondump.1*

%files lib
%defattr(-,root,root,-)
%doc README GNU-AGPL-3.0.txt APACHE-2.0.txt
%{_libdir}/libmongoclient.so

%files server
%defattr(-,root,root,-)
%{_bindir}/mongod
%{_bindir}/mongos
%{_mandir}/man1/mongod.1*
%{_mandir}/man1/mongos.1*
%dir %attr(0755, %{pkg_name}, root) %{?_scl_root}/var/lib/%{pkg_name}
%dir %attr(0755, %{pkg_name}, root) /var/log/%{?scl_prefix}%{pkg_name}
%dir %attr(0755, %{pkg_name}, root) %{?_scl_root}/var/run/%{pkg_name}
%config(noreplace) /etc/logrotate.d/%{?scl_prefix}%{name}
%config(noreplace) %{_sysconfdir}/mongodb.conf
%config(noreplace) %{_sysconfdir}/sysconfig/%{daemon}
/lib/systemd/system/*.service
/usr/lib/tmpfiles.d/%{?scl_prefix}mongodb.conf

%{_mandir}/man1/mongod.1*

%files devel
%defattr(-,root,root,-)
%{_includedir}

%changelog
* Tue Jun 11 2013 Honza Horak <hhorak@redhat.com> - 2.2.3-6
- Fix some SCL paths

* Sat Apr 20 2013 Honza Horak <hhorak@redhat.com> - 2.2.3-5
- Packaged as Software collection package

* Wed Mar 27 2013 Troy Dawson <tdawson@redhat.com> - 2.2.3-4
- Fix for CVE-2013-1892

* Sun Feb 10 2013 Denis Arnaud <denis.arnaud_fedora@m4x.org> - 2.2.3-3
- Rebuild for Boost-1.53.0

* Sat Feb 09 2013 Denis Arnaud <denis.arnaud_fedora@m4x.org> - 2.2.3-2
- Rebuild for Boost-1.53.0

* Tue Feb 05 2013 Troy Dawson <tdawson@redhat.com> - 2.2.3-1
- Update to version 2.2.3

* Mon Jan 07 2013 Troy Dawson <tdawson@redhat.com> - 2.2.2-2
- remove duplicate headers (#886064)

* Wed Dec 05 2012 Troy Dawson <tdawson@redhat.com> - 2.2.2-1
- Updated to version 2.2.2

* Tue Nov 27 2012 Troy Dawson <tdawson@redhat.com> - 2.2.1-3
- Add ssl build option
- Using the reserved mongod UID for the useradd
- mongod man page in server package (#880351)
- added optional MONGODB_OPTIONS to init script

* Wed Oct 31 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.2.1-2
- Make sure build and install flags are the same
- Actually remove the js patch file

* Wed Oct 31 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.2.1-1
- Remove fork fix patch (fixed upstream)
- Remove pcre patch (fixed upstream)
- Remove mozjs patch (now using v8 upstream)
- Update to 2.2.1

* Tue Oct 02 2012 Troy Dawson <tdawson@redhat.com> - 2.2.0-6
- full flag patch to get 32 bit builds to work 

* Tue Oct 02 2012 Troy Dawson <tdawson@redhat.com> - 2.2.0-5
- shared libraries patch
- Fix up minor %files issues

* Fri Sep 28 2012 Troy Dawson <tdawson@redhat.com> - 2.2.0-4
- Fix spec files problems

* Fri Sep 28 2012 Troy Dawson <tdawson@redhat.com> - 2.2.0-3
- Updated patch to use system libraries
- Update init script to use a pidfile

* Thu Sep 27 2012 Troy Dawson <tdawson@redhat.com> - 2.2.0-2
- Added patch to use system libraries

* Wed Sep 19 2012 Troy Dawson <tdawson@redhat.com> - 2.2.0-1
- Updated to 2.2.0
- Updated patches that were still needed
- use v8 instead of spider_monkey due to bundled library issues

* Tue Aug 21 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.7-1
- Update to 2.0.7
- Don't patch for boost-filesystem version 3 on EL6

* Mon Aug 13 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.6-3
- Remove EL5 support
- Add patch to use boost-filesystem version 3

* Wed Aug 01 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.6-2
- Don't apply fix-xtime patch on EL5

* Wed Aug 01 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.6-1
- Update to 2.0.6
- Update no-term patch
- Add fix-xtime patch for new boost

* Fri Jul 20 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.0.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Tue Apr 17 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.4-1
- Update to 2.0.4
- Remove oldpython patch (fixed upstream)
- Remove snappy patch (fixed upstream)

* Tue Feb 28 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.0.2-10
- Rebuilt for c++ ABI breakage

* Fri Feb 10 2012 Petr Pisar <ppisar@redhat.com> - 2.0.2-9
- Rebuild against PCRE 8.30

* Fri Feb 03 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.2-8
- Disable HTTP interface by default (#752331)

* Fri Feb 03 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.2-7
- Enable journaling by default (#656112)
- Remove BuildRequires on unittest (#755081)

* Fri Feb 03 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.2-6
- Clean up mongodb-src-r2.0.2-js.patch and fix #787246

* Tue Jan 17 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.2-5
- Enable build using external snappy

* Tue Jan 17 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.2-4
- Patch buildsystem for building on older pythons (RHEL5)

* Mon Jan 16 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.2-3
- Merge the 2.0.2 spec file with EPEL
- Merge mongodb-sm-pkgconfig.patch into mongodb-src-r2.0.2-js.patch

* Mon Jan 16 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.2-2
- Add pkg-config enablement patch

* Thu Jan 14 2012 Nathaniel McCallum <nathaniel@natemccallum.com> - 2.0.2-1
- Update to 2.0.2
- Add new files (mongotop and bsondump manpage)
- Update mongodb-src-r1.8.2-js.patch => mongodb-src-r2.0.2-js.patch
- Update mongodb-fix-fork.patch
- Fix pcre linking

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.8.2-11
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Sun Nov 20 2011 Chris Lalancette <clalancette@gmail.com> - 1.8.2-10
- Rebuild for rawhide boost update

* Thu Sep 22 2011 Chris Lalancette <clalance@redhat.com> - 1.8.2-9
- Copy the right source file into place for tmpfiles.d

* Tue Sep 20 2011 Chris Lalancette <clalance@redhat.com> - 1.8.2-8
- Add a tmpfiles.d file to create the /var/run/mongodb subdirectory

* Mon Sep 12 2011 Chris Lalancette <clalance@redhat.com> - 1.8.2-7
- Add a patch to fix the forking to play nice with systemd
- Make the /var/run/mongodb directory owned by mongodb

* Thu Jul 28 2011 Chris Lalancette <clalance@redhat.com> - 1.8.2-6
- BZ 725601 - fix the javascript engine to not hang (thanks to Eduardo Habkost)

* Mon Jul 25 2011 Chris Lalancette <clalance@redhat.com> - 1.8.2-5
- Fixes to post server, preun server, and postun server to use systemd

* Thu Jul 21 2011 Chris Lalancette <clalance@redhat.com> - 1.8.2-4
- Update to use systemd init

* Thu Jul 21 2011 Chris Lalancette <clalance@redhat.com> - 1.8.2-3
- Rebuild for boost ABI break

* Wed Jul 13 2011 Chris Lalancette <clalance@redhat.com> - 1.8.2-2
- Make mongodb-devel require boost-devel (BZ 703184)

* Fri Jul 01 2011 Chris Lalancette <clalance@redhat.com> - 1.8.2-1
- Update to upstream 1.8.2
- Add patch to ignore TERM

* Fri Jul 01 2011 Chris Lalancette <clalance@redhat.com> - 1.8.0-3
- Bump release to build against new boost package

* Sat Mar 19 2011 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.8.0-2
- Make mongod bind only to 127.0.0.1 by default

* Sat Mar 19 2011 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.8.0-1
- Update to 1.8.0
- Remove upstreamed nonce patch

* Wed Feb 16 2011 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.7.5-5
- Add nonce patch

* Sun Feb 13 2011 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.7.5-4
- Manually define to use boost-fs v2

* Sat Feb 12 2011 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.7.5-3
- Disable extra warnings

* Fri Feb 11 2011 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.7.5-2
- Disable compilation errors on warnings

* Fri Feb 11 2011 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.7.5-1
- Update to 1.7.5
- Remove CPPFLAGS override
- Added libmongodb package

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.6.4-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Mon Dec 06 2010 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.6.4-3
- Add post/postun ldconfig... oops!

* Mon Dec 06 2010 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.6.4-2
- Enable --sharedclient option, remove static lib

* Sat Dec 04 2010 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.6.4-1
- New upstream release

* Fri Oct 08 2010 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.6.3-4
- Put -fPIC onto both the build and install scons calls

* Fri Oct 08 2010 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.6.3-3
- Define _initddir when it doesn't exist for el5 and others

* Fri Oct 08 2010 Nathaniel McCallum <nathaniel@natemccallum.com> - 1.6.3-2
- Added -fPIC build option which was dropped by accident

* Thu Oct  7 2010 Ionuț C. Arțăriși <mapleoin@fedoraproject.org> - 1.6.3-1
- removed js Requires
- new upstream release
- added more excludearches: sparc s390, s390x and bugzilla pointer

* Tue Sep  7 2010 Ionuț C. Arțăriși <mapleoin@fedoraproject.org> - 1.6.2-2
- added ExcludeArch for ppc

* Fri Sep  3 2010 Ionuț C. Arțăriși <mapleoin@fedoraproject.org> - 1.6.2-1
- new upstream release 1.6.2
- send mongod the USR1 signal when doing logrotate
- use config options when starting the daemon from the initfile
- removed dbpath patch: rely on config
- added pid directory to config file and created the dir in the spec
- made the init script use options from the config file
- changed logpath in mongodb.conf

* Wed Sep  1 2010 Ionuț C. Arțăriși <mapleoin@fedoraproject.org> - 1.6.1-1
- new upstream release 1.6.1
- patched SConstruct to allow setting cppflags
- stopped using sed and chmod macros

* Fri Aug  6 2010 Ionuț C. Arțăriși <mapleoin@fedoraproject.org> - 1.6.0-1
- new upstream release: 1.6.0
- added -server package
- added new license file to %%docs
- fix spurious permissions and EOF encodings on some files

* Tue Jun 15 2010 Ionuț C. Arțăriși <mapleoin@fedoraproject.org> - 1.4.3-2
- added explicit js requirement
- changed some names

* Wed May 26 2010 Ionuț C. Arțăriși <mapleoin@fedoraproject.org> - 1.4.3-1
- updated to 1.4.3
- added zlib license for util/md5
- deleted upstream deb/rpm recipes
- made scons not strip binaries
- made naming more consistent in logfile, lockfiles, init scripts etc.
- included manpages and added corresponding license
- added mongodb.conf to sources

* Fri Oct  2 2009 Ionuț Arțăriși <mapleoin@fedoraproject.org> - 1.0.0-3
- fixed libpath issue for 64bit systems

* Thu Oct  1 2009 Ionuț Arțăriși <mapleoin@fedoraproject.org> - 1.0.0-2
- added virtual -static package

* Mon Aug 31 2009 Ionuț Arțăriși <mapleoin@fedoraproject.org> - 1.0.0-1
- Initial release.
