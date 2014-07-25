#!/bin/bash

# Use specified or default file as input
if [ "A$1" != "A" ]; then
    infile="$1"
else
    infile="/etc/grid-security/groupmapfile"
fi

# Preface
echo 'resource "http://authz-interop.org/xacml/resource/resource-type/wn" {
   obligation "http://glite.org/xacml/obligation/local-environment-map" {}
         action "http://glite.org/xacml/action/execute" {
'         

# Note: the oder of '-e' clauses in the following sed is important!
    # First: Permit any indicated group/role as pfqan
    # Second: If some /vo/* rule exists, allow '/vo' as any fqan
    #         (assuming '/vo' will always be in the proxy to achieve '*' behaviour)
    # Third: Remove any other '*' rule, since the previous one should cover our '*' cases
sed -e 's@\("[^*]*"\).*@     rule permit {pfqan = \1 }@' \
    -e '/"\/[^/]*\/\*"/s@"\(/.*\)/.*@     rule permit {fqan = "\1" }@' \
    -e '/\*/d'  \
    $infile

# End the policy
echo "     }
}
"
