#!/bin/env ruby

#
# xpdsh.rb -- by Dario Berzano <dario.berzano@cern.ch>
#
# Tool to invoke pdsh (with SSH) on multiple hosts taken from a given list. It
# also takes care of maintaining the known_hosts file and has the possibility to
# check if hosts are reachable before launching pdsh.
#
# Known issues and limitations:
#
#  - it can only connect to port 22;
#  - passwordless SSH assumes a default key location, use PDSH_SSH_ARGS_APPEND
#    (a pdsh, *not* xpdsh environment variable) to override;
#  - connection only happens 
#

require 'pp'
require 'optparse'
require 'socket'

# Exit codes
$err = {
  :show_help      => 1,
  :invalid_regexp => 2,
  :wrong_options  => 3,
  :io_known_hosts => 4,
  :no_hosts       => 5,
  :no_ext_cmd     => 6,
}

# The keys file: path *must* not contain any space
$known_hosts = "#{ENV['HOME']}/.ssh/known_hosts"

# Local domain name (or nil if unavailable)
host_dom = Socket.getaddrinfo(Socket.gethostname, nil).first[2].split('.', 2)
if host_dom.length == 2
  $local_domain = host_dom.last
else
  $local_domain = nil
end
host_dom = nil

# Returns an array with all known names (FQDN, hostname, IP) of the given host
# with respect to the current one (i.e., by taking into account domain name)
def get_host_info(s)

  # Prepare response array of aliases (IP and addresses)
  aliases = []

  # Get information from the given IP or name
  begin
    resp = Socket.getaddrinfo(s, nil)
  rescue
    aliases << s
  else

    fqdn = resp.first[2]
    ip   = resp.first[3]
    aliases << fqdn

    if fqdn != ip
      host_dom = fqdn.split('.', 2)
      if $local_domain && host_dom.length == 2 && host_dom.last == $local_domain
        aliases << host_dom.first
      end
      aliases << ip
    end

  end

  return aliases

end

# Fetch hostkeys from the given list
def fetch_host_keys(hosts_stat, verbose = false)

  #
  # 1. Remove keys from known_hosts, using ssh-keygen -R <host>
  #

  hosts_stat.each do |hs|

    hs[:names].each do |hn|
      system(
        "ssh-keygen -f \"#{$known_hosts}\" -R #{hn} > /dev/null 2> /dev/null" )
    end

  end

  #
  # 2. Fetch new keys using ssh-keyscan
  #

  begin

    $stderr.print "Fetching host keys to #{$known_hosts}:\n  " if verbose

    open($known_hosts, 'a') do |file|

      tot = hosts_stat.length
      count = 1

      hosts_stat.each do |hs|

        if verbose
          pct = 100. * count.to_f / tot.to_f
          $stderr.printf( "\r\033[0K[% 3d%%] %s", pct.round, hs[:names].first )
          $stderr.flush
        end

        keys = %x[ ssh-keyscan -t rsa,dsa #{hs[:names].first} 2> /dev/null ]
        keys.gsub!( hs[:names].first, hs[:names].join(',') )

        file << keys

        count += 1

      end

      file.close

    end

    warn "\r\033[0KDone!" if verbose

  rescue
    return false
  end

  return true

end

# Check if SSH is up. Check is performed using nc in zero I/O mode (fast), or by
# attempting to ssh (deep). Check status is appended to the input array of
# hashes
def check_hosts(hosts_stat, deep = false, verbose = true)

  $stderr.print "Checking which hosts are up:\n  " if verbose

  tot = hosts_stat.length
  count = 1

  hosts_stat.each do |hs|

    if verbose
      pct = 100. * count.to_f / tot.to_f
      $stderr.printf( "\r\033[0K[% 3d%%] %s", pct.round, hs[:names].first )
      $stderr.flush
    end

    hn = hs[:names].first

    if deep
      rnd = (rand()*10000000).round()
      hs[:up] = %x[ ssh -oUserKnownHostsFile=#{$known_hosts} \
        -oConnectTimeout=5 #{hn} echo #{rnd} 2> /dev/null ].include?(rnd.to_s)
    else
      hs[:up] = system("nc -z #{hn} 22 2> /dev/null > /dev/null")
    end

    count += 1

  end

  warn "\r\033[0KDone!" if verbose

end

# The main function
def main

  prog = File.basename($0)
  opts = {
    :skipoff    => true,
    :regexp     => nil,  # nil matches all
    :check      => true,
    :deep_check => false,
    :fetch_keys => false,
    :connect    => true,
  }

  # Parse options
  op = OptionParser.new do |op|

    op.on('-h', '--help', 'shows usage') do
      warn op
      exit $err[:show_help]
    end

    op.on('-r', '--filter REGEXP',
      'only connect to hosts matching REGEXP') do |r|
      begin
        opts[:regexp] = Regexp.new(r)
      rescue RegexpError => e
        warn "Invalid regexp: #{e.message}"
        exit $err[:invalid_regexp]
      end
    end

    op.on('-c', '--[no-]check',
      "check if host is up beforehand (default: #{opts[:check]})") do |check|
      opts[:check] = check
    end

    op.on('-k', '--[no-]fetch-keys', "fetch SSH keys (implies '-o')") do
      opts[:fetch_keys] = true
      opts[:check] = true
      opts[:connect] = false
    end

    op.on('-o', '--check-only', "only check, no connection (implies '-c')") do
      opts[:check] = true
      opts[:connect] = false
    end

    op.on('-d', '--[no-]deep-check', "if checking, perform a slower " +
      "host check (default: #{opts[:deep_check]})") do |deep_check|
      opts[:deep_check] = deep_check
    end

  end

  # Custom banner
  op.banner = "#{prog} -- by Dario Berzano <dario.berzano@cern.ch>\n" +
    "A smart pdsh wrapper.\n\n" +
    "Usage: #{prog} [options]"

  # Parse options
  begin
    op.parse!
  rescue OptionParser::ParseError => e
    warn "#{prog}: arguments error: #{e.message}"
    exit $err[:wrong_options]
  end

  #
  # Here, we fetch the list of hosts somehow...
  #

  hosts_cmd = ENV['XPDSH_LIST_CMD']
  unless hosts_cmd
    warn 'You should export the XPDSH_LIST_CMD environment variable ' +
      'containing a command to execute in order to retrieve the hosts list.'
    exit $err[:no_ext_cmd]
  end

  hosts_all = %x[ #{hosts_cmd} ].split("\n")
  hosts_all.sort!
  hosts_all.uniq!

  # Trim input, remove empty lines, remove lines not matching regexp
  re_match = true
  hosts_all.delete_if do |h|
    h.strip!
    h.empty? or (opts[:regexp] != nil and not opts[:regexp] =~ h)
  end

  # Hosts are put into a hash
  hosts_stat = []
  hosts_all.each do |h|
    hosts_stat << { :names => get_host_info(h) }
  end
  hosts_all = nil

  #
  # Fetch SSH keys
  #

  if opts[:fetch_keys]
    unless fetch_host_keys( hosts_stat, true )
      warn "Can't write keys to file #{$known_hosts}!"
      exit $err[:io_known_hosts]
    end
  end

  #
  # Check hosts up
  #

  check_hosts( hosts_stat, opts[:deep_check], true ) if opts[:check]

  #
  # Join list of hosts up
  #

  hosts_up = []
  hosts_down = []
  hosts_stat.each do |h|
    if h[:up] != false
      hosts_up << h[:names].first
    else
      hosts_down << h[:names].first
    end
  end

  if hosts_up.length > 0
    warn "Hosts up (#{hosts_up.length}):"
    warn hosts_up.join(' ')
  end

  if hosts_down.length > 0
    warn "Hosts down (#{hosts_down.length}):"
    warn hosts_down.join(' ')
  elsif hosts_up.length > 0
    warn 'All hosts seem up!'
  end

  #
  # Connect with pdsh
  #

  if opts[:connect]
    if hosts_up.length > 0
      exec(
        "export PDSH_SSH_ARGS_APPEND='-oUserKnownHostsFile=#{$known_hosts}';" +
        "pdsh -R ssh -l #{ENV['USER']} -w #{hosts_up.join(',')}" )
    else
      warn 'No hosts are up, exiting'
      exit $err[:no_hosts]
    end
  end

end

#
# Entry point
#

main
