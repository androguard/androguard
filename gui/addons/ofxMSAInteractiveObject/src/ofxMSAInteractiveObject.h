/***********************************************************************

 Copyright (c) 2008, 2009, 2010, Memo Akten, www.memo.tv
 *** The Mega Super Awesome Visuals Company ***
 * All rights reserved.
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


#pragma once

#include "ofMain.h"


class ofxMSAInteractiveObject : public ofRectangle {
public:
	bool		enabled;				// set this to false to temporarily disable all events
	bool		verbose;

	ofxMSAInteractiveObject();			// constructor
	virtual ~ofxMSAInteractiveObject();	// destructor

	void enableAllEvents();				// enable all event callbacks
	void disableAllEvents();			// disable all event callbacks

	void enableMouseEvents();			// call this if object should receive mouse events
	void disableMouseEvents();			// call this if object doesn't need to receive mouse events (default)

	void enableKeyEvents();				// call this if object should receive key events
	void disableKeyEvents();			// call this if object doesn't need to receive key events (default)

	void enableAppEvents();				// call this if object should update/draw automatically	(default)
	void disableAppEvents();			// call this if object doesn't need to update/draw automatically

	void setPos(float _x, float _y);	// set position of object
	void setSize(float _w, float _h);	// set size of object

	void setPosAndSize(float _x, float _y, float _w, float _h);		// set pos and size

	bool isMouseOver();					// returns true if mouse is over object (based on position and size)
	bool isMouseDown();					// returns true if mouse button is down and over object (based on position and size)
	int	 getMouseX();					// returns mouse X (in screen coordinates)
	int  getMouseY();					// returns mouse Y (in screen coordinates)
	int  getLastMouseButton();			// returns last mouse button to have activity

	virtual bool hitTest(int tx, int ty);		// returns true if given (x, y) coordinates (in screen space) are over the object (based on position and size)

	void killMe();						// if your object is a pointer, and you are done with it, call this


	// extend ofxMSAInteractiveObject and override all or any of the following methods
	virtual void setup()	{}	// called when app starts
	virtual void update()	{}	// called every frame to update object
    virtual void draw()		{}	// called every frame to draw object
	virtual void exit()		{}	// called when app quites

	// these behave very similar to those in flash
	virtual void onRollOver(int x, int y)					{}		// called when mouse enters object x, y, width, height
	virtual void onRollOut()								{}		// called when mouse leaves object x, y, width, height
	virtual void onMouseMove(int x, int y)					{}		// called when mouse moves while over object x, y, width, height
	virtual void onDragOver(int x, int y, int button)		{}		// called when mouse moves while over object and button is down
	virtual void onDragOutside(int x, int y, int button)	{}		// called when mouse moves while outside the object after being clicked on it
	virtual void onPress(int x, int y, int button)			{}		// called when mouse presses while over object
	virtual void onPressOutside(int x, int y, int button)	{}		// called when mouse presses while outside object
	virtual void onRelease(int x, int y, int button)		{}		// called when mouse releases while over object
	virtual void onReleaseOutside(int x, int y, int button)	{}		// called when mouse releases outside of object after being pressed on object

	virtual void keyPressed( int key ){}
	virtual void keyReleased( int key ){}


	// you shouldn't need access to any of these unless you know what you are doing
	// (i.e. disable auto updates and call these manually)
	void _setup(ofEventArgs &e);
	void _update(ofEventArgs &e);
    void _draw(ofEventArgs &e);
	void _exit(ofEventArgs &e);

	void _mouseMoved(ofMouseEventArgs &e);
	void _mousePressed(ofMouseEventArgs &e);
	void _mouseDragged(ofMouseEventArgs &e);
	void _mouseReleased(ofMouseEventArgs &e);

	void _keyPressed(ofKeyEventArgs &e);
	void _keyReleased(ofKeyEventArgs &e);


protected:
	int			_mouseX, _mouseY, _mouseButton;
	bool		_mouseOver;
	bool		_mouseDown;
	ofRectangle	oldRect;
};

