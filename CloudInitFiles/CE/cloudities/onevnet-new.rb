#!/usr/bin/ruby

#
# onevnet-new.rb -- by Dario Berzano <dario.berzano@cern.ch>
#
# Used to create a new vnet for OpenNebula. It creates the template and
# also adds the hosts to Cobbler.
#

require 'pp'
require 'optparse'
require 'ipaddr'
#require 'tempfile'

# Commands
$cmds = {

  # Order of strings: 0=>name 1=>prof 2=>mac 3=>ip 4=>name.full
  :cobbler => "system add --name %s --profile %s " \
              "--mac-address %s --ip-address %s --dns-name %s " \
              "--netboot-enabled 0",

  # Default Cobbler command (local machine)
  # Override with envvar ONEVNET_NEW_COBBLERCMD
  :cobbler_stdin => "T=$(mktemp /tmp/onevnet-new-cobbler-XXXXX) ; " \
                    "grep -v '^cobbler$' | while read Cmd ; do " \
                    "eval cobbler \"$Cmd\" || exit 1 ; done && " \
                    "cobbler sync > /dev/null 2>&1",

  # Example of possible Cobbler command on a remote host (use helper there!)
  #:cobbler_stdin => "ssh t2-se-00.to.infn.it -l root " \
  #                  "-i /home/oneadmin/.ssh/id_rsa-cobbler-t2-se-00 -q -T",

  # Default onevnet create command (local machine)
  # Override with envvar ONEVNET_NEW_VNETCMD
  :onevnet_stdin => "T=$(mktemp /tmp/onevnet-new-vnet-XXXXX) ; " \
                    "grep -v '^onevnet$' | cat > $T ; " \
                    "onevnet create $T && rm -f $T",

}

# Error conditions
$err = {
  :help       =>  1,
  :invalidip  =>  2,
  :invalidmac =>  3,
  :args       =>  4,
  :nobasename =>  5,
  :nonetname  =>  6,
  :iovnet     =>  7,
  :iocobbler  =>  8,
  :addrclass  =>  9,
  :noaddr     => 10,
}

# Extremely simple and incomplete class to handle a MAC address
class MacAddr

  def initialize(mac)

    case mac

      when String

        if (mac.match(/[^0-9a-f:]/i))
          raise Exception.new("Invalid format for MacAddr: #{mac}")

        elsif (mac.include?(':'))

          # Couplets separated by colons
          @mac_i = 0
          mac_ary = mac.split(':').each do |ff|
            @mac_i = (@mac_i << 8) | (ff.to_i(16) & 0xff)
          end

        else

          # Hexadecimal integer in ASCII
          @mac_i = Integer( '0x' + mac ) #& 0xffffffffffff

        end

      when Integer

        @mac_i = mac #& 0xffffffffffff

      else
        raise Exception.new("Invalid argument type for MacAddr: #{mac.class}")

    end

      # Check if too big
      if ((@mac_i < 0) || (@mac_i > 0xffffffffffff))
        raise Exception.new("Address out of range for MacAddr: " \
          "#{@mac_i.to_s(16)}")
      end

  end

  def to_s
    str = @mac_i.to_s(16)
    pre = 12 - str.length
    str = '0' * pre + str if (pre > 0)
    str_sep = ''

    (0..10).step(2) do |i|
      str_sep << ':' unless (i == 0)
      str_sep << str[i,2]
    end

    return str_sep
  end

  def +(n)
    return self.class.new(@mac_i + n)
  end

  def -(n)
    return self+(-n)
  end

end

# Extends class IPAddr functionalities
class IPAddr

  # Returns a new IPAddr instance  whose IP is the mask of the current IPAddr
  def bitmask
    return IPAddr.new(_to_string(@mask_addr))
    #ip.inspect.match(/\/([0-9\.]+)>/)
  end

  # Returns the mask as a number of bytes
  def bitmask_n
    mask = @mask_addr
    count = 32
    while ( (mask & 0x1) == 0 )
      mask = mask >> 1
      count = count - 1
    end
    return count
  end

end

# The main function
def main

  prog = File.basename($0)
  opts = {
    :name        => nil,
    :bridge      => 'br0',
    :vlan        => false,
    :basemac     => MacAddr.new('02:00:00:00:00:00'),
    :iprange     => IPAddr.new('192.168.0.0/24'),
    :cobblerprof => '00-AfakeProf',
    :domain      => nil,
    :basename    => nil,
    :docblr      => false,
    :dovnet      => true,
    :commit      => false,
    :skip        => [],
  }

  # Options taken
  OptionParser.new do |op|

    op.on('-h', '--help', 'shows usage') do
      warn op
      exit $err[:help]
    end

    op.on('-r', '--range IP', "IP mask (default: #{opts[:iprange]})") do |ip|
      begin
        opts[:iprange] = IPAddr.new(ip)
      rescue Exception => e
        warn "#{prog}: invalid IP range specification: #{e.message}"
        exit $err[:invalidip]
      end
    end

    op.on('-m', '--mac MAC',
      "base MAC address (default: #{opts[:basemac]})") do |mac|
      begin
        opts[:basemac] = MacAddr.new(mac)
      rescue Exception => e
        warn "#{prog}: invalid MAC address: #{e.message}"
        exit $err[:invalidmac]
      end
    end

    op.on('-i', '--[no-]isolation', "isolates network, i.e.: VLAN=Yes " \
     "in OpenNebula (default: #{opts[:vlan]})") do |isol|
      opts[:vlan] = isol
    end

    op.on('-p', '--cobbler-profile PROFILE', "associated Cobbler " \
      "fake profile (default: #{opts[:cobblerprof]})") do |prof|
      opts[:cobblerprof] = prof
    end

    op.on('-d', '--domain DOMAIN', 'DNS domain for added hosts') do |dom|
      opts[:domain] = dom
    end

    op.on('-b', '--base-name BASENAME', 'host base name') do |base|
      opts[:basename] = base
    end

    op.on('-n', '--net-name NETNAME', 'network name') do |netname|
      opts[:name] = netname
    end

    op.on('-c', '--[no-]cobbler',
      "invokes cobbler (default: #{opts[:docblr]})") do |cblr|
      opts[:docblr] = cblr
    end

    op.on('-o', '--[no-]onevnet',
      "invokes onevnet (default: #{opts[:dovnet]})") do |vnet|
      opts[:dovnet] = vnet
    end

    op.on('--[no-]commit', "invokes commands as opposed to " \
      "printing to screen (default: #{opts[:commit]})") do |commit|
      opts[:commit] = commit
    end

    op.on('-s', '--skip-addr 0,255,bcast', Array,
      'skips IP addresses ending with .0, .255 and broadcast adresses') do |ary|

      ary.each do |skip|

        case skip
          when '0'
            opts[:skip] << :addr0
          when '255'
            opts[:skip] << :addr255
          when 'bcast'
            opts[:skip] << :addrbcast
          else
            warn "#{prog}: invalid address class: #{skip}"
            exit $err[:addrclass]
        end

      end

    end

    # Custom banner
    op.banner = "#{prog} -- by Dario Berzano <dario.berzano@cern.ch>\n" \
     "Creates a new vnet for OpenNebula and adds hosts to Cobbler\n\n" \
     "If you don't use --commit, output might be very large: you can then " \
     "redirect stdout to a file to save it, since all error messages are on " \
     "stderr.\n\n" \
     "By default, cobbler and onevnet are invoked locally, unless you set " \
     "envvars ONEVNET_NEW_[COBBLERCMD,VNETCMD].\n\n" \
     "Usage: #{prog} [options]"

    # Parse options
    begin
      op.parse!
    rescue OptionParser::ParseError => e
      warn "#{prog}: arguments error: #{e.message}"
      exit $err[:args]
    end

  end

  # Missing arguments?
  if (opts[:basename] == nil)
    warn "#{prog}: you must provide a host base name"
    exit $err[:nobasename]
  elsif (opts[:name] == nil)
    warn "#{prog}: you must provide a network name"
    exit $err[:nonetname]
  end

  # Override onevnet and Cobbler commands with envvar?
  cblr = ENV['ONEVNET_NEW_COBBLERCMD']
  $cmds[:cobbler_stdin] = cblr unless ((cblr == nil) || (cblr == ''))

  vnet = ENV['ONEVNET_NEW_VNETCMD']
  $cmds[:onevnet_stdin] = vnet unless ((vnet == nil) || (vnet == ''))

  # All IPs and base MAC to increment
  range = opts[:iprange].to_range.to_a

  #opts[:skip].uniq!

  if (opts[:skip].include?(:addr0))
    range = range.select do |ip|
      (ip.to_i % 256) != 0
    end
  end

  if (opts[:skip].include?(:addr255))
    range = range.select do |ip|
      (ip.to_i % 256) != 255
    end
  end

  if (opts[:skip].include?(:addrbcast))
    range.pop
  end

  # Count the number of addresses left
  if (range.count == 0)
    warn "#{prog}: no IP available: try not skipping IP addresses with -s"
    exit $err[:noaddr]
  end

  # Name format
  name_fmt = sprintf("#{opts[:basename]}%%0%uu", Math.log10(range.count).ceil)

  # Prints a small report
  warn "IP range: #{range.min}..#{range.max}"
  warn "IP mask: #{opts[:iprange].bitmask} (#{opts[:iprange].bitmask_n})"
  warn "Number of hosts: #{range.count}"
  warn "Example FQDN of a host: " + \
    sprintf(name_fmt, 1) + (opts[:domain] ? '.' + opts[:domain] : '')
  warn "MAC range: #{opts[:basemac]+range.min.to_i}.." \
    "#{opts[:basemac]+range.max.to_i}"

  # OpenNebula virtual network section
  if (opts[:dovnet])

    begin

      if (opts[:commit])
        vnet_fp = IO.popen($cmds[:onevnet_stdin], 'w')
        vnet_fp.puts 'onevnet'  # header for the helper
      else
        #vnet_fp = Tempfile.new('vnet')
        vnet_fp = $stdout
      end

      vnet_fp.puts "NAME = #{opts[:name]}"
      vnet_fp.puts "TYPE = FIXED"
      vnet_fp.puts "BRIDGE = #{opts[:bridge]}"
      vnet_fp.puts "VLAN = " + (opts[:vlan] ? 'Yes' : 'No')
      range.each do |ip|
        vnet_fp.puts "LEASES = [IP=#{ip}, " \
          "MAC=#{(opts[:basemac] + ip.to_i).to_s.upcase}]"
      end

      if (opts[:commit])
        vnet_fp.close
        if ($? != 0)
          raise Exception.new("error executing command to add vnet " \
            "(returned #{$? >> 8})")
        end
      end

    rescue Exception => e
      warn "#{prog}: I/O error writing net template: #{e.message} (#{e.class})"
      exit $err[:iovnet]
    end

  end

  # Cobbler command
  if (opts[:docblr])

    count = 0

    begin

      if (opts[:commit])
        cobbler_fp = IO.popen($cmds[:cobbler_stdin], 'w')
        cobbler_fp.puts 'cobbler'  # header for the helper
      else
        cobbler_fp = $stdout
      end

      range.each do |ip|

        count += 1

        name = sprintf(name_fmt, count)
        fqdn = name
        fqdn << '.' << opts[:domain] if (opts[:domain] != nil)

        # Order of strings: 0=>name 1=>prof 2=>mac 3=>ip 4=>fqdn
        args = [
          name,
          opts[:cobblerprof],
          (opts[:basemac] + ip.to_i).to_s.upcase,
          ip,
          fqdn,
        ]

        cobbler_fp.printf( $cmds[:cobbler] + "\n", *args )

      end

      if (opts[:commit])
        cobbler_fp.close
        if ($? != 0)
          raise Exception.new("error executing command to add Cobbler hosts " \
            "(returned #{$? >> 8})");
        end
      end

    rescue Exception => e
      warn "#{prog}: I/O error in Cobbler: #{e.message} (#{e.class})"
      exit $err[:iocobbler]
    end

  end # if cobbler

end

#
# Entry point
#

main
