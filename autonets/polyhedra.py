#! /usr/bin/env python
'''
Copyright (C) 2010 Jonathan Manton (jmanton @ illinois.edu)
Copyright (C) 2007 Aaron Spike  (aaron @ ekips.org)
Copyright (C) 2007 Tavmjong Bah (tavmjong @ free.fr)

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''

# this program is loosely based on the gear extension for inkscape

import inkex
from polyhedrondata import angleOverride, polyhedronData
import simplestyle, sys
from math import *

def points_to_svgd(p):
    f = p[0]
    p = p[1:]
    svgd = 'M%.3f,%.3f' % f
    for x in p:
        svgd += 'L%.3f,%.3f' % x
    return svgd

# these are designed to be 100px wide - they have to be scaled
no_tab = { 'cut' : ['m 0,0 100,0'], 'perf' : []}

notab = {0 : no_tab}
simpletab = {0: {'cut': ['m 0,0 20,19 60,0 l 20,-19'], 'perf' : ['m 0,0 100,0']}}
# tab array - 0 = slot/tab, 1 = two tabs, 2 = single tab (alternate tab and nothing), 3 = none
tabStyle = [{ \
	50 : {'cut': ['m 0,0 35,0 0,2 -6,0 c 0,0 1,8 6,12 8,6 22,6 30,0 5,-4 6,-12 6,-12 l -6,0 0,-2 35,0'], 'perf' : ['M 42,0 58,0']}, \
	24 : {'cut': ['m 0,0 55,0 0,2 -6,0 c 0,0 1,3 6,6 8,3 19,6 27,8 5,-4 9,-14 9,-14 l -6,0 0,-2 15,0'], 'perf' : ['M 62,0 78,0']}, \
	18 : {'cut' : ['m 0,0 65,0 0,2 -6,0 c 0,0 1,3 6,6 8,2 11,2 19,3 5,-4 9,-10 7,-9 l -6,0 0,-2 15,0'], 'perf' : ['m 72,0 6,0']}, \
	6 : {'cut': ['m 0,0 70,0 2,7 10,1 5,-6 -2,0 0,-2 15,0'], 'perf' : ['m 74,0 7,0']}, 
	0 : { 'cut' : ['m 0,0 100,0'], 'perf' : []}}, simpletab, simpletab, notab]
slotStyle = [{\
	50: {'cut': ['m 0,0 20,19 60,0 l 20,-19','m 28,-3 4,5 36,0 4,-5'], 'perf' : ['M 0,0 28,0','M 100,0 72,0']}, \
	24 : {'cut': ['M 100,0 90,18 30,11 20,0 0,0', 'm 92,-3 -4,5 -36,0 -4,-5'], 'perf' : ['M 100,0 92,0', 'M 20,0 48,0']}, \
	18 : {'cut' : ['M 100,0 90,16 40,9 35,0 0,0', 'm 92,-3 -4,5 -26,0 -4,-5'], 'perf' : ['M 100,0 92,0', 'M 35,0 58,0']}, \
	6 : {'cut' : ['M 100,0 98,10 88,9 84,2 86,2 86,0 0,0'], 'perf' : ['m 96,0 -6,0']},
	0 : { 'cut' : ['m 0,0 100,0'], 'perf' : [] }}, simpletab, notab, notab]


class Polyhedra(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.OptionParser.add_option("-p", "--poly",
                        action="store", type="string",
                        dest="poly", default='Cube',
                        help="polygon net to render")
        self.OptionParser.add_option("-s", "--size",
                        action="store", type="float",
                        dest="size", default=100.0,
                        help="size of first edge, in px")
        self.OptionParser.add_option("-t", "--tabs",
                        action="store", type="int",
                        dest="tabs", default=0,
                        help="tab style")

    def get_tab(self, limitAngle):
	return(self.get_connector('tab', limitAngle))

    def get_slot(self, limitAngle):
	return(self.get_connector('slot', limitAngle))

    def get_connector(self, type, limitAngle):

	if(self.options.tabs == 1):	# two tabs
		return(self.gen_tab(limitAngle/2))

	if(self.options.tabs == 2):	# one tab
		if(type == 'tab'):
			return(self.gen_tab(limitAngle))
		else:
			return(no_tab)

	if(self.options.tabs == 3):	# no tabs or slots
		return(no_tab)
		
	# otherwise, get stuff from the array of specially modified tab/slots 

	if(type == 'tab'):
		source = tabStyle
	else:
		source = slotStyle

	cuttable = source[self.options.tabs].keys()
	cuttable.sort()			# sorts in-place.  Ugh.
	cuttable.reverse()		# in-place.  Ugh.
	for angle in cuttable:
		if(limitAngle >= angle):
			return(source[self.options.tabs][angle])

    def gen_tab(self, theta_degrees):
	theta = radians(min(theta_degrees,90))
	minOffset = 8
	tabAngle = radians(40)
	minTabLength = 40
	tabHeight = 19  # must be >= minOffset
	tabWidth = 100

	# determine if we need to sqash down side of tab by limit angle
	bX = minOffset * cos(theta) / sin(theta)
	aX = bX - (minOffset * cos(tabAngle) / sin(tabAngle))
	if(theta >= tabAngle):
		tab_cut = [(0,0), (tabHeight/sin(tabAngle) * cos(tabAngle), tabHeight)]
		tab_perf = [(0,0), (tabWidth,0)]
	else:
		if (aX > (tabWidth - minTabLength)):	# too stubby, don't put a tab
			return(no_tab)
		tab_cut = [(0,0), (aX,0), (bX, minOffset)]
		tab_perf = [(aX,0), (tabWidth,0)]

	# now see if we also have to squash the other side of the tab - this happens
	# for very small angles where the tab height on the far side would still be
	# too high and would intersect with the other tab

	# first, find where the tab would intersect the limit angle if we just put
	# out a line of infinite length at the tab angle.
	bmult = tabWidth / (cos(theta) * sin(tabAngle) / sin(theta) + cos(tabAngle))
	tiY = bmult * sin(tabAngle)

	# now see if that intersection is too low.  If so, limit the tab's height
	tiY = min(tiY, tabHeight)
	tab_cut.append((tabWidth - tiY / sin(tabAngle) * cos(tabAngle), tiY))
	tab_cut.append((tabWidth, 0))
	
	return({'cut' : [points_to_svgd(tab_cut)], 'perf' : [points_to_svgd(tab_perf)]})
	
    def effect(self):

	poly = self.options.poly
	size = self.options.size

	eC = polyhedronData[poly]['edgeCoordinates']
	iEI = polyhedronData[poly]['insideEdgeIndices']
	oEI = polyhedronData[poly]['outsideEdgeIndices']
	oED = polyhedronData[poly]['outsideEdgeDegrees']
	sidelen = sqrt((eC[oEI[0][0]-1][0] - eC[oEI[0][1]-1][0])**2 + \
				(eC[oEI[0][0]-1][1] - eC[oEI[0][1]-1][1])**2)
	scale = size / sidelen


        #  Translate group, Rotate path.
        t = 'translate(' + str( self.view_center[0] ) + ',' + str( self.view_center[1] ) + ')'
        g_attribs = {inkex.addNS('label','inkscape'):'Polygon ' + str( poly ),
                     'transform':t }
        g = inkex.etree.SubElement(self.current_layer, 'g', g_attribs)

	gsub_attribs = {inkex.addNS('label','inkscape'):'Polygon ' + str( poly ) + 'border' }
        gsub = inkex.etree.SubElement(g, 'g', gsub_attribs)

        # Create SVG Path for gear
        cutStyle = { 'stroke': '#0000FF', 'fill': 'none' }
        perfStyle = { 'stroke': '#FF0000', 'fill': 'none' }
	textStyle = {
          'font-size': str( size/4 ),
          'font-family': 'arial',
          'text-anchor': 'middle',
          'text-align': 'center',
          'fill': '#222'
          }

	numOEI = len(oEI)
	for edgeIndex in range(numOEI):
		eX1 = eC[oEI[edgeIndex][0]-1][0]
		eY1 = eC[oEI[edgeIndex][0]-1][1]
		eX2 = eC[oEI[edgeIndex][1]-1][0]
		eY2 = eC[oEI[edgeIndex][1]-1][1]

		origin = (eX1 * scale, eY1 * scale)
		edgelen = sqrt((eX1 - eX2)**2 + (eY1 - eY2)**2)
		edgesize = size * (edgelen / sidelen)


		prevAngle = (oED[(edgeIndex - 1) % numOEI] + 180 - oED[edgeIndex]) % 360
		nextAngle = (oED[edgeIndex] + 180 - oED[(edgeIndex + 1) % numOEI]) % 360
		if angleOverride.has_key(poly):
			if angleOverride[poly].has_key('prev'):
				if angleOverride[poly]['prev'].has_key(edgeIndex):
					prevAngle = angleOverride[poly]['prev'][edgeIndex]
			if angleOverride[poly].has_key('next'):
				if angleOverride[poly]['next'].has_key(edgeIndex):
					nextAngle = angleOverride[poly]['next'][edgeIndex]
		trans = 'translate(' + str(origin[0]) + ',' + str(origin[1]) + ') rotate(' + str(oED[edgeIndex] ) + ') scale(' + str(edgesize/100.0) + ')' 

		limitAngle = min(prevAngle, nextAngle)
		tab = self.get_tab(limitAngle)
		slot = self.get_slot(limitAngle)

		# the "special" tabs are all skewed one way or the other, to 
		# make room for tight turns.  This determines if it is the previous
		# or next angle that is the tight one, and flips the tab or slot if
		# needed.

		if(nextAngle == limitAngle):
			trans += ' translate(100.0, 0) scale(-1,1)'

		tab_group_attribs = {inkex.addNS('label','inkscape'):'tab', 'transform': trans }
        	tab_group = inkex.etree.SubElement(gsub, 'g', tab_group_attribs)
		midX = (eX2 - eX1)/2 + eX1
		midY = (eY2 - eY1)/2 + eY1
		text_attrib = {'style': simplestyle.formatStyle(textStyle),
			'x' : str(midX * scale), 'y' : str(midY * scale) }
		# inkex.etree.SubElement(gsub, 'text', text_attrib).text = str(edgeIndex)
		if ((edgeIndex % 2) == 0):
			edgetype = tab
		else:
			edgetype = slot

		for path in edgetype['cut']:
        		gear_attribs = {'style':simplestyle.formatStyle(cutStyle), 'd':path}
        		gear = inkex.etree.SubElement(tab_group, inkex.addNS('path','svg'), gear_attribs )

		for path in edgetype['perf']:
        		gear_attribs = {'style':simplestyle.formatStyle(perfStyle), 'd':path}
        		gear = inkex.etree.SubElement(tab_group, inkex.addNS('path','svg'), gear_attribs )
	
	gsub_attribs = {inkex.addNS('label','inkscape'):'Polygon ' + str( poly ) + 'inside' }
        gsub = inkex.etree.SubElement(g, 'g', gsub_attribs)

	for edge in iEI:
		points = [(eC[edge[0]-1][0] * scale, eC[edge[0]-1][1] * scale), (eC[edge[1]-1][0] * scale, eC[edge[1]-1][1] * scale)]
        	path = points_to_svgd( points )
        	perf_attribs = {'style':simplestyle.formatStyle(perfStyle), 'd':path}
        	gear = inkex.etree.SubElement(gsub, inkex.addNS('path','svg'), perf_attribs )

if __name__ == '__main__':
    e = Polyhedra()
    e.affect()


# vim: expandtab shiftwidth=4 tabstop=8 softtabstop=4 encoding=utf-8 textwidth=99
