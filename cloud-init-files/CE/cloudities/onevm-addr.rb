#!/bin/env ruby

#
# onevm-addr.rb -- by Dario Berzano <dario.berzano@cern.ch>
#
# Shows the list of currently running VMs along with their assigned IP
# addresses.
#

require 'pp'
require 'socket'
require 'optparse'

# Using libxml gem
require 'rubygems'
gem "libxml-ruby", "~> 2.3.2"
require 'libxml'
include LibXML
XML::Error.set_handler(&XML::Error::QUIET_HANDLER)

#
# Global variables and traps
#

# Local domain name (or nil if unavailable)
host_dom = Socket.getaddrinfo(Socket.gethostname, nil).first[2].split('.', 2)
if host_dom.length == 2
  $local_domain = host_dom.last
else
  $local_domain = nil
end
host_dom = nil

$sleep_res_s = 0.2
$sleep_s = 1.4
$sleep_loops = $sleep_s / $sleep_res_s
$exit_nicely = false

# Color codes
$col = {
  :y => "\e[33m",
  :r => "\e[31m",
  :g => "\e[32m",
  :b => "\e[34m",
  :m => "\e[35m",
  :c => "\e[36m",
  :z => "\e[0m"
}

# States strings (possibly colored)
$states_str = [
  $col[:c] + 'init',
  $col[:y] + 'pend',
             'hold',
  $col[:g] + 'actv',
             'stop',
             'susp',
  $col[:g] + 'done',
  $col[:r] + 'fail'
]

# VM life-cycle manager states to strings
$lcm_states_str = [
  $col[:c] + 'init',  # 0
  $col[:y] + 'prol',  # 1
  $col[:b] + 'boot',  # 2
  $col[:g] + 'runn',  # 3
  $col[:m] + 'migr',  # 4
             'stop',  # 5
             'susp',  # 6
             'smgr',  # 7
             'pmgr',  # 8
             'prsm',  # 9
             'estp',  # 10
  $col[:b] + 'epil',  # 11
  $col[:m] + 'shut',  # 12
             'canc',  # 13
  $col[:r] + 'fail',  # 14
             'dele',  # 15
  $col[:y] + 'unkn'   # 16
]

# Append escape sequence to stop coloring
$states_str.each_index { |i| $states_str[i] += $col[:z] }
$lcm_states_str.each_index { |i| $lcm_states_str[i] += $col[:z] }

# Ping statuses
$ping_stat_str = {
  :unknown => 'unknown',
  :failure => 'no',
  :success => 'yes'
}

#
# Initialization
#

# Catch Ctrl+C and handle it gracefully
trap('INT') { $exit_nicely = true }

#
# Functions
#

# Print a formatted table of stuff
def print_table(columns, data, print_headings = true)

  # Fill base lengths
  columns.each do |col|
    col[:length] = (print_headings ? col[:title].length : 0)
  end

  # Compute maximum length of each field
  data.each do |datum|

    columns.each do |col|
      if (col[:func] != nil)
        str = col[:func].call(datum).to_s
      else
        str = datum[col[:key]].to_s
      end
      str = str.gsub(/\e\[[0-9;]*m/, '')  # eliminate "colors"
      col[:length] = [ col[:length], str.length ].max
    end

  end

  # Create the format string
  table_format_row = '|'
  columns.each do |col|
    if (col[:type] == :int)
      table_format_row << sprintf(" %%%dd |", col[:length])
    else
      table_format_row << sprintf(" %%-%ds |", col[:length])
    end
  end
  table_format_row << "\n"

  # Special line: title
  table_format_title = "\e[1m\e[4m" +
    table_format_row.gsub(/%-?([0-9]+)[a-z]/, '%-\1s').gsub(/\|/, ' ') + "\e[m"

  # Create the horizontal line
  table_horizontal = '+'
  columns.each do |col|
    table_horizontal << '-' * (col[:length]+2) << '+'
  end

  # Print table
  if (print_headings)
    titles = []
    columns.each do |col|
      titles << col[:title]
    end
    #puts table_horizontal
    printf(table_format_title, *titles);
  else
    puts table_horizontal
  end

  data.each do |datum|
    cols_ary = []
    columns.each do |col|
      if (col[:func])
        cols_ary << col[:func].call(datum)
      else
        cols_ary << datum[col[:key]]
      end
    end
    printf(table_format_row, *cols_ary)
    #puts table_horizontal
  end
  puts table_horizontal

end

# Returns FQDN from given IP, or nil if not found
def get_fqdn(ip)
  begin
    resp = Socket.getaddrinfo(ip, nil)
  rescue
    return nil
  end
  fqdn = resp[0][2]
  nip  = resp[0][3]
  return nil if (fqdn == nip)
  return fqdn
end

# Pings some host: true on success, false elsewhere
def ping?(what)
  return system("ping -c1 -W2 -q #{what} > /dev/null 2> /dev/null")
end

# Gets the list of ONE VMs along with their leased IPs and hostnames
def get_onevms(ping = false)

  vms = []

  begin
    #xml_parser = XML::Parser.string( %x[ cat /tmp/onevm-list.xml ] )
    xml_parser = XML::Parser.string( %x[ onevm list -x ] )
    xml_doc = xml_parser.parse
  rescue
    #return nil
    return []
  end

  while xml_doc.next?
    puts xml_doc.next.class
  end

  xml_doc.find('//VM_POOL/VM').each do |xml_vm|

    # These must exist
    xml_id = xml_vm.find_first('ID') or next
    xml_name = xml_vm.find_first('NAME') or next
    xml_stat = xml_vm.find_first('STATE') or next
    xml_lcm_stat = xml_vm.find_first('LCM_STATE') or next

    xml_hyperv = xml_vm.find_first('HISTORY_RECORDS/HISTORY/HOSTNAME')

    addr = []
    xml_vm.find('TEMPLATE/NIC').each do |xml_nic|
      xml_ip = xml_nic.find_first('IP') or next
      ip = xml_ip.content
      addr << {
        :ip => ip,
        :host => get_fqdn(ip),
        :ping => ping ? ping?(ip) : nil,
      }
    end

    vm = {
      :id => xml_id.content.to_i,
      :name => xml_name.content,
      :hyperv => xml_hyperv ? xml_hyperv.content : '',
      :stat => xml_stat.content.to_i,
      :lcmstat => xml_lcm_stat.content.to_i,
      :addr => addr
    }

    vms << vm

  end

  return vms

end

# Print VM information
def print_vminfo(vmary, clear = false, datetime = false)

  columns = [
    { :key => :id, :title => 'VMID', :type => :int },
    { :key => :name, :title => 'Name', :type => :string },
    { :key => :stat, :title => 'Stat', :type => :string,
      :func => lambda { |record| return $states_str[record[:stat]] }
    },
    { :key => :lcmstat, :title => 'LCM', :type => :string,
      :func => lambda { |record| return $lcm_states_str[record[:lcmstat]] }
    },
    { :key => :hyperv, :title => 'Hypervisor', :type => :string },
    { :key => :addr, :title => 'Leased addresses', :type => :string,
      :func => lambda { |r|

        known_names = []

        r[:addr].each do |addr|
          #known_names << addr[:host] if addr[:host]
          known_names << addr[:ip] if addr[:ip]

          # Separate host from domain name
          if addr[:host]
            host_dom = addr[:host].split('.', 2)
            if $local_domain && host_dom.length == 2 &&
               host_dom.last == $local_domain
              known_names << host_dom.first  # we are in the same domain
            else
              known_names << addr[:host]
            end
          end

        end

        known_names.uniq.sort.join(', ')
      }
    },
  ]

  print "\e[H\e[2J" if clear
  print Time.now.to_s + " / every #{$sleep_s}s\n\n" if datetime

  print_table(columns, vmary)

end

# Main function
def main

  prog = File.basename($0)
  opts = {
    :top => false,
    :ping => false,
  }

  # Parse command-line args
  OptionParser.new do |op|

    op.on('-h', '--help', 'prints help screen') do
      puts op
      exit 3
    end

    op.on('-p', '--[no-]ping',
      "attempts to ping host (default: #{opts[:ping]})") do |ping|
      opts[:ping] = ping
    end

    op.on('-t', '--[no-]top',
      "top mode (default: #{opts[:top]})") do |top|
      opts[:top] = top
    end

    # Custom banner
    op.banner = "#{prog} -- by Dario Berzano <dario.berzano@cern.ch>\n" \
      "Parses and summarizes information returned by pbsnodes.\n\n" \
       "Use the environment variable PBSINFO_PBSNODES_CMD to specify the " \
      "command used to retrieve XML output of pbsnodes. If none is given " \
      "a reasonable default is used.\n\n" \
      "Usage: #{prog} [options]"

    # Parse options
    begin
      op.parse!
    rescue OptionParser::ParseError => e
      puts "#{prog}: arguments error: #{e.message}"
      exit 1
    end

  end

  if opts[:top]
    # Top mode
    until $exit_nicely
      print_vminfo(get_onevms(opts[:ping]), true, true)
      for i in 0..$sleep_loops
        sleep $sleep_res_s
        break if $exit_nicely
      end
    end
  else
    # One shot
    print_vminfo( get_onevms(opts[:ping]) )
  end

end

#
# Entry point
#

main
