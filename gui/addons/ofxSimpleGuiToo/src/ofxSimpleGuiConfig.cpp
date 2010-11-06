/***********************************************************************

 Copyright (c) 2008, 2009, 2010, Memo Akten, www.memo.tv
 *** The Mega Super Awesome Visuals Company ***
 * All rights reserved.

 based on Todd Vanderlin's ofxSimpleGui API
 http://toddvanderlin.com/

 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 *     * Redistributions of source code must retain the above copyright
 *       notice, this list of conditions and the following disclaimer.
 *     * Redistributions in binary form must reproduce the above copyright
 *       notice, this list of conditions and the following disclaimer in the
 *       documentation and/or other materials provided with the distribution.
 *     * Neither the name of MSA Visuals nor the names of its contributors
 *       may be used to endorse or promote products derived from this software
 *       without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
 * THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
 * OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
 * OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
 * OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 * ***********************************************************************/


#include "ofxSimpleGuiConfig.h"

ofxSimpleGuiConfig defaultSimpleGuiConfig;


ofxSimpleGuiConfig::ofxSimpleGuiConfig() {
	
	sliderHeight		= 10;
	sliderTextHeight	= 36;
	titleHeight			= sliderHeight + sliderTextHeight;
	toggleHeight		= titleHeight;
	buttonHeight		= titleHeight;
	slider2DTextHeight	= titleHeight * 1.5;
	comboBoxHeight		= titleHeight;	//15
	comboBoxTextHeight	= 15;
	
	
	padding.set			(titleHeight/2, 10);
	offset.set			(titleHeight/2, titleHeight/2);
	slider2DSize.set	(titleHeight * 4, titleHeight * 4);
	
	gridSize.x			= 200 + padding.x;
	gridSize.y			= toggleHeight + padding.y;
	
	textColor			= 0x888888;
	textOverColor		= 0xFFFFFF;
	textBGColor			= 0x000000;
	textBGOverColor		= 0x222222;
	
	fullColor			= 0xaaaaaa;
	fullOverColor		= 0xffffff;
	fullActiveColor		= 0x881818;
	emptyColor			= 0x333333;
	
	borderColor			= 0x333333;
}