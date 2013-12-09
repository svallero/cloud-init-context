#!/bin/env ruby

#
# pbsinfo.rb -- by Dario Berzano <dario.berzano@cern.ch>
#
# This script exploits XML output of pbsnodes to summarize various information
# about the facility.
#

#
# Global variables and requirements
#

# Minimal requirements
require 'pp'
require 'optparse'
require 'rexml/document'
#require 'rexml/formatters/pretty'

# Default command to retrieve pbsnodes XML output: if defined, environment
# variable PBSINFO_PBSNDOES_CMD will be used instead
$pbsnodes_cmd = 'pbsnodes -x'

# Global pretty formatter
#$xml_formatter = REXML::Formatters::Pretty.new

#
# Functions
#

# Parse info for a node and returns a hash containing node info
def parse_node(node_xml)

  # name, state, np, properties, ntype, jobs, status
  #$xml_formatter.write(node_xml, $stdout)

  node = {}

  node[:name] = node_xml.elements['name'].text
  node[:np] = node_xml.elements['np'].text.to_i
  #node[:state] = node_xml.elements['state'].text.split(',')
  node[:state] = node_xml.elements['state'].text

  if ((jobs = node_xml.elements['jobs']) != nil)
    node[:jobs] = jobs.text.split(' ')
  else
    node[:jobs] = []
  end

  return node

end

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
  table_format_title = table_format_row.gsub(/%-?([0-9]+)[a-z]/, '%-\1s')

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
    puts table_horizontal
    printf(table_format_title, *titles);
  end

  puts table_horizontal

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

# The main function
def main

  prog = File.basename($0)
  whatout = :full
  include_offline = false;
  include_down = false;

  # Parse command-line args
  OptionParser.new do |op|

    op.on('-h', '--help', 'prints help screen') do
      puts op
      exit 3
    end

    op.on('-s', '--slots', 'total number of slots') do
      whatout = :slots
    end

    op.on('-j', '--jobs', 'number of running jobs') do
      whatout = :jobs
    end

    op.on('-f', '--free', 'number of free slots') do
      whatout = :free
    end

    op.on('-r', '--report',
      'prints out a formatted table with jobs and slots summary') do
      whatout = :report
    end

    op.on('-n', '--nodes',
      'prints out the list of nodes with information in a formatted table') do
      whatout = :nodes
    end

    op.on('-a', '--full', 'full report with list of nodes and summary') do
      whatout = :full
    end

    op.on('-o', '--[no-]offline', "includes offline nodes in total and " \
      "free slots count (default: #{include_offline})") do |off|
      include_offline = off
    end

    op.on('-d', '--[no-]down', "includes down nodes in total and " \
      "free slots count (default: #{include_down})") do |down|
      include_down = down
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

  # Retrieve command from PBSINFO_PBSNDOES_CMD envvar, if set
  pbsinfo_cmd_env = ENV['PBSINFO_PBSNODES_CMD']
  if ((pbsinfo_cmd_env != nil) && (pbsinfo_cmd_env.length > 0))
    $pbsnodes_cmd = pbsinfo_cmd_env
    #warn "Using custom command:"
    #warn "  #{$pbsnodes_cmd}"
  end

  begin
    pbsnodes_xml = REXML::Document.new( %x[ #{$pbsnodes_cmd} ] )
  rescue Exception => e
    warn "Can not retrieve pbsnodes output, sorry (#{e.message})"
    exit 1
  end

  if (pbsnodes_xml.elements.empty?)
    warn "Command returned no parsable output, sorry"
    exit 2
  end

  # Pretty format XML on stdout
  #$xml_formatter.write(pbsnodes_xml, $stdout)

  # Array of columns
  columns = [
    { :key => :name,  :title => 'node',  :type => :string },
    { :key => :over,  :title => 'jobs',  :type => :string,
      :func => lambda { |n|
      return sprintf('%2d/%2d', n[:jobs].length.to_s, n[:np].to_s) } },
    { :key => :state, :title => 'state', :type => :string },
    #{ :key => :jobs,  :title => 'jobs',  :type => :string,
    #  :func => lambda { |n|
    #    jobs_ary = []
    #    n[:jobs].each do |job|
    #      m = /\/([0-9]+)\./.match(job)
    #      if (m)
    #        jobs_ary << m.captures[0]
    #      end
    #    end
    #    return jobs_ary.join(',')
    #  } }
  ]

  # Array of nodes
  nodes = []

  # Statistics
  tot_slots = 0
  tot_jobs = 0

  # Parse the list of nodes
  pbsnodes_xml.elements.each('//Data/Node') do |node_xml|

    node = parse_node(node_xml)
    nodes << node

    # If node is down and we told to skip, don't count in total jobs either!
    next if (!include_down) && (node[:state].include?('down'))

    # Fill statistics
    tot_jobs += node[:jobs].length

    # Check whether to count offline and down nodes
    next if (!include_offline) && (node[:state].include?('offline'))

    tot_slots += node[:np]

  end

  free_slots = tot_slots-tot_jobs

  # Columns for the report table
  columns_report = [
    { :key => :name, :type => :string },
    { :key => :val,  :type => :int },
  ]
  values_report = [
    { :name => 'Total slots',   :val => tot_slots },
    { :name => 'Total jobs',    :val => tot_jobs },
    { :name => 'Free slots',    :val => free_slots },
  ]

  # Sort nodes by name
  nodes = nodes.sort_by { |h| h[:name] }

  # All nodes
  case whatout

    when :nodes
      print_table(columns, nodes)

    when :report
      print_table(columns_report, values_report, false)

    when :full
      print_table(columns, nodes)
      print_table(columns_report, values_report, false)

    when :slots
      puts tot_slots

    when :jobs
      puts tot_jobs

    when :free
      puts free_slots

  end 

end

#
# Entry point
#

main
