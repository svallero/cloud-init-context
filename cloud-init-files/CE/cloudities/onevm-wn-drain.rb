#!/bin/env ruby

#
# onevn-wn-drain.rb -- by Dario Berzano <dario.berzano@cern.ch>
#
# Drains PBS nodes from the queue and, when appropriate, from OpenNebula.
#

#
# Global variables and requirements
#

# Minimal requirements
require 'pp'
require 'optparse'
require 'rexml/document'
require 'socket'
#require 'rexml/formatters/pretty'

# Commands to invoke
$cmd_pbsnodes = 'pbsnodes -x'  # override with envvar PBSINFO_PBSNDOES_CMD
$cmd_delnode = 'false'  # override with envvar PBSINFO_DELNODE_CMD
$cmd_offnode = 'false'  # override with envvar PBSINFO_OFFNODE_CMD

# Loop sleep (seconds)
$loop_sleep_sec = 60

# How many errors in retrieving njobs before eliminating node from the list
$err_threshold = 3

# Global pretty formatter
#$xml_formatter = REXML::Formatters::Pretty.new

#
# Functions
#

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

# Append Torque job count to the nodes list
def get_njobs(nodes)

  # Reset job count on each input node
  nodes.each do |wn|
    wn[:njobs] = -1
  end

  begin
    pbsnodes_xml = REXML::Document.new( %x[ #{$cmd_pbsnodes} 2> /dev/null ] )
  rescue
    return
  end

  return if pbsnodes_xml.elements.empty?

  pbsnodes_xml.elements.each('//Data/Node') do |node_xml|

    name = node_xml.elements['name'].text
    is_offline = node_xml.elements['state'].text.include?('offline')
    is_down = node_xml.elements['state'].text.include?('down')

    jobs_xml = node_xml.elements['jobs']
    if jobs_xml
      njobs = jobs_xml.text.split(' ').length
    else
      njobs = 0
    end

    # Find matching input nodes: FQDN must be set, node must be up and offline
    nodes.each do |wn|
      next unless wn[:fqdn] and wn[:fqdn] == name and is_offline and !is_down
      wn[:njobs] = njobs
    end

  end

end

# Append OpenNebula VMID to nodes list
def get_vmids(nodes)

  one_xml = REXML::Document.new( %x[ onevm list -x ] )
  #one_xml = REXML::Document.new( %x[cat /home/oneadmin/test_input.xml] )

  one_xml.elements.each('//VM_POOL/VM') do |vm_xml|

    vmid_xml = vm_xml.get_elements('ID').first
    next unless vmid_xml

    ip_xml = vm_xml.get_elements('TEMPLATE/NIC[1]/IP').first
    next unless ip_xml

    vmid = Integer(vmid_xml.text)
    ip = ip_xml.text

    fqdn = get_fqdn(ip)
    next unless fqdn

    nodes.each do |wn|
      next unless wn[:fqdn] == fqdn
      wn[:vmid] = vmid
    end

  end

end

# Trivial logging facility with date and time prepended
def say(*fmt)
  print Time.now.localtime.strftime('[%Y%m%d-%H%M%S] ')
  printf *fmt
  puts ''
end

# Print node status
def pn(n)

  vmid = n[:vmid]
  vmid = '<unk>' unless vmid

  fqdn = n[:fqdn]
  fqdn = '<unk>' unless fqdn

  njobs = n[:njobs]
  njobs = '<unk>' if njobs == -1

  errcount = n[:errcount]

  say("Node #{n[:name]} (#{fqdn}) with VMID #{vmid} has #{njobs} jobs(s) " \
    "and #{errcount} error(s)")
end

# The main function
def main

  prog = File.basename($0)
  nodes = []

  # Parse command-line args
  OptionParser.new do |op|

    op.on('-h', '--help', 'prints help screen') do
      warn op
      exit 3
    end

    op.on('-n', '--names wn1,wn2...', Array, 'list of nodes to drain') do |ary|
      ary.uniq!
      ary.sort!
      ary.each do |wn_name|
        nodes << {
          :name => wn_name,
          :errcount => 0,
        }
      end

    end

    op.on('-t', '--threshold THR', Integer, "number of consecutive failures " \
      "before giving up on a node (default: #{$err_threshold})") do |thr|
      if thr < 1
        raise OptionParser::ParseError.new('only numbers >= 1 accepted')
      end
      $err_threshold = thr
    end

    op.on('-s', '--sleep THR', Integer,
      "seconds to sleep between loops (default: #{$loop_sleep_sec})") do |sl|
      if sl < 4
        raise OptionParser::ParseError.new('must sleep at least 4 seconds')
      end
      $loop_sleep_sec = sl
    end

    # Custom banner
    op.banner = "#{prog} -- by Dario Berzano <dario.berzano@cern.ch>\n" \
      "Puts a PBS virtual worker node in drain mode: node is set offline and " \
      "the corresponding OpenNebula virtual machine is shut down when no " \
      "more jobs are running.\n\n" \
      "Environment variables:\n" \
      "    PBSINFO_PBSNDOES_CMD: the 'pbsinfo -x' command\n" \
      "    PBSINFO_DELNODE_CMD: command to delete node\n" \
      "    PBSINFO_OFFNODE_CMD: command to set node offline\n\n" \
      "Usage: #{prog} [options]"

    # Parse options
    begin
      op.parse!
    rescue OptionParser::ParseError => e
      warn "#{prog}: arguments error: #{e.message}"
      exit 1
    end

  end

  # No nodes given?
  if nodes.length == 0
    warn 'No nodes given! Use -n to specify a list of nodes to drain'
    exit 1
  end

  # Retrieve commands from envvars when possible
  $cmd_pbsnodes = ENV['PBSINFO_PBSNODES_CMD'] if ENV['PBSINFO_PBSNODES_CMD']
  $cmd_delnode = ENV['PBSINFO_DELNODE_CMD'] if ENV['PBSINFO_DELNODE_CMD']
  $cmd_offnode = ENV['PBSINFO_OFFNODE_CMD'] if ENV['PBSINFO_OFFNODE_CMD']

  # Find FQDNs
  nodes.each do |wn|
    fqdn = get_fqdn(wn[:name])
    wn[:fqdn] = fqdn if fqdn
  end

  # Attach VMIDs (a node can have no VMID associated)
  get_vmids(nodes)

  # Set the nodes offline
  nodes.each do |wn|
    if wn[:fqdn]
      say "Setting node #{wn[:name]} (#{wn[:fqdn]}) offline"
      system("echo #{wn[:fqdn]} | #{$cmd_offnode} > /dev/null 2>&1")
    else
      say "Node #{wn[:name]} has no FQDN, can't set it offline"
    end
  end

  # Prepare arrays for successes and failures
  nodes_ok = []
  nodes_err = []

  begin

    while nodes.length > 0

      say '=== Getting nodes statuses ==='

      # Get number of jobs from PBS
      get_njobs(nodes)

      # Check for errors
      nodes.delete_if do |n|
        n[:errcount] += 1 if n[:njobs] == -1
        pn n

        if n[:errcount] >= $err_threshold

          #
          # Consecutive error threshold reached
          #

          say "Node #{n[:name]} removed: too many consecutive " \
            "errors (#{$err_threshold})"

          nodes_err << n[:name]
          true # remove

        elsif n[:njobs] == 0

          #
          # Jobs count eventually reached zero
          #

          say "No more jobs on node #{n[:name]}"
          say ">> Removing node #{n[:fqdn]} from the queues..."
          system("echo #{n[:fqdn]} | #{$cmd_delnode} > /dev/null 2>&1")
          if n[:vmid] != nil

            if system("onevm shutdown #{n[:vmid]} > /dev/null 2>&1")
              say ">> OpenNebula VM #{n[:vmid]} shut down"
              nodes_ok << n[:name]
              true # remove
            else
              say ">> Error shutting down OpenNebula VM #{n[:vmid]}"
              n[:errcount] += 1
              nodes_err << n[:name]
              false # don't remove
            end

          else
            # Node is not virtual (or no VMID found...)
            nodes_ok << n[:name]
            true # remove
          end

        else

          #
          # Nothing to do: reset error count
          #

          n[:errcount] = 0 unless n[:njobs] == -1
          false # don't remove

        end

      end # delete_if

      # Sleeping
      say "Sleeping #{$loop_sleep_sec} seconds..."
      sleep $loop_sleep_sec

    end

  rescue Interrupt
    say 'Terminating as per user request'
  end

  # Final report
  say '=== Final report ==='
  say "Nodes drained successfully: #{nodes_ok.join(',')}" if nodes_ok.length > 0
  say "Nodes with errors: #{nodes_err.join(',')}" if nodes_err.length > 0
  if nodes.length > 0
    nodes_left = []
    nodes.each do |n|
      nodes_left << n[:name]
    end
    say "Nodes still waiting: #{nodes_left.join(',')}"
  end

end

#
# Entry point
#

main
