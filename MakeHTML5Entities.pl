#!/usr/bin/perl
#

# Create a name2codepoint dict for python using the *complete* list of
# HTML5 entities downloaded from the w3 org website.
#

use strict;
use warnings;

use LWP::Simple qw( get );

# Get the web page...
#
my $resp = get('https://dev.w3.org/html5/html-author/charref');
exit unless defined $resp;

# We get lines like this (wrapped here):
#   <tr title="U+00009 CHARACTER TABULATION" data-block="C0 Controls and Basic Latin"
#    data-category="Cc" data-set="mmlextra"><td class="character"> &#x00009;
#    <td class="named"><code>&amp;Tab;</code><td class="hex"><code>&amp;#x00009;
#    </code><td class="dec"><code>&amp;#9;</code><td class="desc">CHARACTER TABULATION
#
# The class="named" section may contain multiple, space-separated entity names.
# Creating a mapping of all entities for each hexcode
#
my %names4;
foreach my $ln (split "\n", $resp) {
    next unless $ln =~ /^<tr/;  # Skip if not a table row
# First we have to translate &amp; to &
#
    $ln =~ s/&amp;/&/g;
# Now extract the name(s) and hex code
#
    my ($nstr, $hexc) =
         ($ln =~ q%\"named\"><code>(.*?)</code>.*?\"hex\"><code>&#(.*?);%);
    $names4{$hexc} = $nstr;
}

# Print out the python file header
#
print <<'EOH';
# This is the full HTML5 Entity list from:
#   https://dev.w3.org/html5/html-author/charref
# This IS case sensitive!!
# The name2codepoint in htmlentitydefs is incomplete.
#
name2codepoint = {
EOH

# Now print out the name for the hex-code in ascending order
# We order them by hex code and handle any multiple entity names
# by writing multiple lines, one for each name.
#
my $nents = 0;
my $nchars = 0;
foreach my $hx (sort keys %names4) {
    $nchars++;
    foreach my $nm (split " ", $names4{$hx}) {
        $nents++;
        my $ent = substr($nm, 1, -1);
        printf "    %-34s : 0%s,\n", "'$ent'", $hx;
    }
}

# Now print the closing brace for the python file
#
print <<'EOF';
}
EOF

# Display stats on STDERR
#
print STDERR "Found $nents entries for $nchars chars\n";
