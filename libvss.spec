# TODO: Run test suite (don't use e3?)
# TODO: Regenerate UCD file?

# The test suite isn't normally run as some of the test data must be downloaded
# separately. It can be enabled with "--with=check".
%bcond_with check

# Upstream source information.
%global upstream_owner    AdaCore
%global upstream_name     VSS
%global upstream_version  24.0.0
%global upstream_gittag   v%{upstream_version}

Name:           libvss
Version:        %{upstream_version}
Release:        1%{?dist}
Summary:        High level string and text processing library

License:        Apache-2.0 WITH LLVM-Exception AND Unicode-DFS-2016
# LibVSS itself is licensed under Apache 2.0 with a runtime exception. The
# Unicode license is mentioned as Unicode data files were used as an input for
# generating some of LibVSS' source code.

URL:            https://github.com/%{upstream_owner}/%{upstream_name}
Source0:        %{url}/archive/%{upstream_gittag}/%{upstream_name}-%{upstream_version}.tar.gz

# Test data. See "data/README.md" on how to create.
#
# +--------------------------------------------------------+-------------+
# | Contents                                               | License     |
# +--------------------------------------------------------+-------------+
# | https://www.unicode.org/Public/15.0.0/ucd/UCD.zip      | Unicode-3.0 |
# | https://github.com/nigeltao/parse-number-fxx-test-data | Apache-2.0  |
# | https://github.com/json5/json5-tests.git               | MIT         |
# +--------------------------------------------------------+-------------+
#
%if %{with check}
Source1:        vss-tests-data.tar.bz2
%endif

BuildRequires:  gcc-gnat gprbuild make sed
# A fedora-gnat-project-common that contains GPRbuild_flags is needed.
BuildRequires:  fedora-gnat-project-common >= 3.17
BuildRequires:  xmlada-devel
%if %{with check}
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-e3-testsuite
%endif

# [Fedora-specific] Set library soname.
Patch:          %{name}-set-soname-of-vss-libraries.patch
# [Fedora-specific] Make build options for tests more flexible.
Patch:          %{name}-build-tests-relocatable.patch

# Build only on architectures where GPRbuild is available.
ExclusiveArch:  %{GPRbuild_arches}

# Compilation of `a-suvsau.adb` and `a-szuvau.adb` fails on GCC 14.0.1 for
# s390x. References parent package are not visible. Seems like a bug in the
# GNAT front-end (non-deterministic behavior across platforms).
ExcludeArch:    s390x

%global common_description_en \
The VSS (as an abbreviation for Virtual String Subsystem) library is \
designed to provide advanced string and text processing capabilities. It \
offers a convenient and robust API that allows developers to work with \
Unicode text, regardless of its internal representation.

%description %{common_description_en}


#################
## Subpackages ##
#################

%package devel
Summary:    Development files for the VSS library
Requires:   %{name}%{?_isa} = %{version}-%{release}
Requires:   fedora-gnat-project-common

%description devel %{common_description_en}

This package contains source code and linking information for developing
applications that use the VSS library.


#############
## Prepare ##
#############

%prep
%autosetup -n %{upstream_name}-%{upstream_version} -p1


###########
## Build ##
###########

%build

# Build the library components.
for component in text gnat json regexp xml xml_templates xml_xmlada; do

    gprbuild %{GPRbuild_flags} \
             -XVERSION=%{version} \
             -XVSS_LIBRARY_TYPE=relocatable \
             -XVSS_BUILD_PROFILE=release \
             -P gnat/vss_${component}.gpr
done;


#############
## Install ##
#############

%install

# Install the library components.
function run_gprinstall {
    local component=$1
    gprinstall --create-missing-dirs --no-manifest --no-build-var \
               --sources-subdir=%{buildroot}%{_includedir}/%{name}-${component} \
               --project-subdir=%{buildroot}%{_GNAT_project_dir} \
               --exec-subdir=%{buildroot}%{_bindir} \
               --ali-subdir=%{buildroot}%{_libdir}/%{name}-${component} \
               --lib-subdir=%{buildroot}%{_libdir} \
               --link-lib-subdir=%{buildroot}%{_libdir} \
               -XVERSION=%{version} \
               -XVSS_LIBRARY_TYPE=relocatable \
               -XVSS_BUILD_PROFILE=release \
               -XXMLADA_BUILD=relocatable \
               -P gnat/vss_${component}.gpr
}

# Install the library components.
for component in text gnat json regexp xml xml_templates xml_xmlada ; do
    run_gprinstall ${component}
done

# Fix up some things that GPRinstall does wrong.
ln --symbolic --force %{name}.so.%{version} \
       %{buildroot}%{_libdir}/%{name}.so

for component in gnat json regexp xml xml-templates xml-xmlada ; do
    ln --symbolic --force %{name}-${component}.so.%{version} \
       %{buildroot}%{_libdir}/%{name}-${component}.so
done


###########
## Check ##
###########

%if %{with check}
%check

# Unpack test data.
pushd ./data
tar --extract --bzip2 --file %{SOURCE1}
popd

# Make the files installed in the buildroot visible to the testsuite.
export LIBRARY_PATH=%{buildroot}%{_libdir}:$LIBRARY_PATH
export LD_LIBRARY_PATH=%{buildroot}%{_libdir}:$LD_LIBRARY_PATH
export GPR_PROJECT_PATH=%{buildroot}%{_GNAT_project_dir}:$GPR_PROJECT_PATH

# Additional flags to link the executables dynamically with the GNAT runtime
# and make the test executables position independent.
%global GPRbuild_flags_pie -cargs -fPIC -largs -pie -bargs -shared -gargs

# Build & run the tests.
make check GPRBUILD_FLAGS='%{GPRbuild_flags} %{GPRbuild_flags_pie}' \
           VERSION=%{version} VSS_LIBRARY_TYPE=relocatable VSS_BUILD_PROFILE=release

%endif


###########
## Files ##
###########

%files
%license LICENSE.txt
%doc README*
%{_libdir}/%{name}.so.%{version}
%{_libdir}/%{name}-gnat.so.%{version}
%{_libdir}/%{name}-json.so.%{version}
%{_libdir}/%{name}-regexp.so.%{version}
%{_libdir}/%{name}-xml.so.%{version}
%{_libdir}/%{name}-xml-templates.so.%{version}
%{_libdir}/%{name}-xml-xmlada.so.%{version}


%files devel
%{_GNAT_project_dir}/vss_text.gpr
%{_includedir}/%{name}-text
%dir %{_libdir}/%{name}-text
%attr(444,-,-) %{_libdir}/%{name}-text/*.ali
%{_libdir}/%{name}.so

%{_GNAT_project_dir}/vss_gnat.gpr
%{_includedir}/%{name}-gnat
%dir %{_libdir}/%{name}-gnat
%attr(444,-,-) %{_libdir}/%{name}-gnat/*.ali
%{_libdir}/%{name}-gnat.so

%{_GNAT_project_dir}/vss_json.gpr
%{_includedir}/%{name}-json
%dir %{_libdir}/%{name}-json
%attr(444,-,-) %{_libdir}/%{name}-json/*.ali
%{_libdir}/%{name}-json.so

%{_GNAT_project_dir}/vss_regexp.gpr
%{_includedir}/%{name}-regexp
%dir %{_libdir}/%{name}-regexp
%attr(444,-,-) %{_libdir}/%{name}-regexp/*.ali
%{_libdir}/%{name}-regexp.so

%{_GNAT_project_dir}/vss_xml.gpr
%{_includedir}/%{name}-xml
%dir %{_libdir}/%{name}-xml
%attr(444,-,-) %{_libdir}/%{name}-xml/*.ali
%{_libdir}/%{name}-xml.so

%{_GNAT_project_dir}/vss_xml_templates.gpr
%{_includedir}/%{name}-xml_templates
%dir %{_libdir}/%{name}-xml_templates
%attr(444,-,-) %{_libdir}/%{name}-xml_templates/*.ali
%{_libdir}/%{name}-xml-templates.so

%{_GNAT_project_dir}/vss_xml_xmlada.gpr
%{_includedir}/%{name}-xml_xmlada
%dir %{_libdir}/%{name}-xml_xmlada
%attr(444,-,-) %{_libdir}/%{name}-xml_xmlada/*.ali
%{_libdir}/%{name}-xml-xmlada.so


###############
## Changelog ##
###############

%changelog
* Mon Jan 29 2024 Dennis van Raaij <dvraaij@fedoraproject.org> - 24.0.0-1
- New package.
