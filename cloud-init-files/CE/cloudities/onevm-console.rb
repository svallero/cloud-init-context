#!/bin/env ruby

#
# onevm-console.rb -- by Dario Berzano <dario.berzano@cern.ch>
#
# Connects to a serial console of the specified virtual host, if available. SSH
# access to the hypervisor should be allowed.
#

#
# No extra gems needed
#

require 'pp'
#require 'socket'
require 'optparse'
require 'rexml/document'

#
# Global variables
#

# Exit codes
$err = {
  :help    => 1,
  :args    => 2,
  :vmid    => 3,
  :vmidnum => 4,
  :giveup  => 5,
  :novmid  => 6,
  :connect => 7,
}

#
# Functions
#

# Get a console for the specified vmid
def get_console(vmid)

  begin
    vm_xml = REXML::Document.new( %x[onevm show #{vmid} -x] )
  rescue
    puts "Cannot find VMID #{vmid}: is OpenNebula up?"
    return nil
  end

  max_seq = -1;
  hyp_name = nil;
  vmm_mad = nil;

  vm_xml.elements.each('//VM/HISTORY_RECORDS/HISTORY') do |hist|

    seq = hist.elements['SEQ']
    if (seq)
      seq = seq.text.to_i
    else
      next
    end

    if (seq > max_seq)
      max_seq = seq
      hyp_name = hist.elements['HOSTNAME']
      vmm_mad = hist.elements['VMMMAD']
      if (hyp_name)
        hyp_name = hyp_name.text
      end
      if (vmm_mad)
        vmm_mad = vmm_mad.text
        vmm_mad = vmm_mad[4..vmm_mad.length-3]
      end
    end

  end

  if (hyp_name != nil)
    puts "Connecting console of VMID #{vmid} from hypervisor #{hyp_name}..."

    if (vmm_mad == 'xen')
      system("ssh #{hyp_name} -t xm console one-#{vmid}")
    else
      system("ssh #{hyp_name} -t " +
        "virsh --connect qemu:///system console one-#{vmid}")
    end

    return ($? >> 8)

  end

  # If we are here, no hypervisor has been found
  #puts "No hypervisor currently associated to VMID #{vmid}."
  return -1

end

# The main function
def main

  prog = File.basename($0)

  opts = {
    :retry => false,
  }

  OptionParser.new do |op|

    op.on('-h', '--help', 'shows usage') do
      warn op
      exit $err[:help]
    end

    op.on('-r', '--[no-]retry',
      "retries until connection succeeds (default: #{opts[:retry]})") do |r|
      opts[:retry] = r
    end

    # Custom banner
    op.banner = "#{prog} -- by Dario Berzano <dario.berzano@cern.ch>\n" \
     "Connects to a serial console associated to the specified VMID\n\n" \
     "Usage: #{prog} [options] VMID"

    # Parse options
    begin
      op.parse!
    rescue OptionParser::ParseError => e
      warn "#{prog}: arguments error: #{e.message}"
      exit $err[:args]
    end

  end

  if (ARGV.length == 0)
    warn "#{prog}: VMID not specified"
    exit $err[:vmid]
  end

  begin
    vmid = Integer(ARGV.first)
  rescue ArgumentError
    warn "#{prog}: VMID must be a number"
    exit $err[:vmidnum]
  end

  if (opts[:retry] === false)

    # Do not retry
    case (get_console(vmid) <=> 0)
      when -1
        warn "#{prog}: cannot find VMID #{vmid}"
        exit $err[:novmid]
      when 1
        warn "#{prog}: cannot connect to VMID #{vmid}"
        exit $err[:connect]
    end

    exit 0

  else

    # Retry
    while true
      ret = get_console(vmid)
      exit 0 if (ret == 0)

      $stderr.print('.')

      begin
        sleep 2
      rescue Interrupt => i
        warn 'giving up'
        exit $err[:giveup]
      end
    end

  end

  # Never reached

end

#
# Entry point
#

main

# Gets the list of ONE VMs along with their leased IPs and hostnames
# #def get_onevms#
# 
#   vms = Array.new
# 
#   begin
#     xml = REXML::Document.new( %x[ onevm list -x ] )
#   rescue
#     return nil
#   end
# 
#   xml.elements.each('//VM_POOL/VM') { |vm|
# 
# end
