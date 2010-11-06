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


#include "ofxMSAInteractiveObject.h"
#include "ofMain.h"

ofxMSAInteractiveObject::ofxMSAInteractiveObject() {
	_mouseOver	= false;
	_mouseDown	= false;
	enabled		= true;
	verbose		= false;
	
	enableAppEvents();
	disableMouseEvents();
	disableKeyEvents();
}

ofxMSAInteractiveObject::~ofxMSAInteractiveObject() {
	disableAllEvents();
}

void ofxMSAInteractiveObject::killMe() {
	delete this;
}

void ofxMSAInteractiveObject::enableAllEvents() {
	enableMouseEvents();
	enableKeyEvents();
	enableAppEvents();
}

void ofxMSAInteractiveObject::disableAllEvents() {
	disableMouseEvents();
	disableKeyEvents();
	disableAppEvents();
}


void ofxMSAInteractiveObject::enableMouseEvents() {
	ofAddListener(ofEvents.mousePressed, this, &ofxMSAInteractiveObject::_mousePressed);
	ofAddListener(ofEvents.mouseMoved, this, &ofxMSAInteractiveObject::_mouseMoved);
	ofAddListener(ofEvents.mouseDragged, this, &ofxMSAInteractiveObject::_mouseDragged);
	ofAddListener(ofEvents.mouseReleased, this, &ofxMSAInteractiveObject::_mouseReleased);
}

void ofxMSAInteractiveObject::disableMouseEvents() {
	ofRemoveListener(ofEvents.mousePressed, this, &ofxMSAInteractiveObject::_mousePressed);
	ofRemoveListener(ofEvents.mouseMoved, this, &ofxMSAInteractiveObject::_mouseMoved);
	ofRemoveListener(ofEvents.mouseDragged, this, &ofxMSAInteractiveObject::_mouseDragged);
	ofRemoveListener(ofEvents.mouseReleased, this, &ofxMSAInteractiveObject::_mouseReleased);
}

void ofxMSAInteractiveObject::enableKeyEvents() {
	ofAddListener(ofEvents.keyPressed, this, &ofxMSAInteractiveObject::_keyPressed);
	ofAddListener(ofEvents.keyReleased, this, &ofxMSAInteractiveObject::_keyReleased);
}

void ofxMSAInteractiveObject::disableKeyEvents() {
	ofRemoveListener(ofEvents.keyPressed, this, &ofxMSAInteractiveObject::_keyPressed);
	ofRemoveListener(ofEvents.keyReleased, this, &ofxMSAInteractiveObject::_keyReleased);
}

void ofxMSAInteractiveObject::enableAppEvents() {
	ofAddListener(ofEvents.setup, this, &ofxMSAInteractiveObject::_setup);
	ofAddListener(ofEvents.update, this, &ofxMSAInteractiveObject::_update);
	ofAddListener(ofEvents.draw, this, &ofxMSAInteractiveObject::_draw);
	ofAddListener(ofEvents.exit, this, &ofxMSAInteractiveObject::_exit);
}

void ofxMSAInteractiveObject::disableAppEvents() {
	ofRemoveListener(ofEvents.setup, this, &ofxMSAInteractiveObject::_setup);
	ofRemoveListener(ofEvents.update, this, &ofxMSAInteractiveObject::_update);
	ofRemoveListener(ofEvents.draw, this, &ofxMSAInteractiveObject::_draw);
	ofRemoveListener(ofEvents.exit, this, &ofxMSAInteractiveObject::_exit);
}


void ofxMSAInteractiveObject::setPos(float _x, float _y) {
	x = _x;
	y = _y;
}

void ofxMSAInteractiveObject::setSize(float _w, float _h) {
	width = _w;
	height = _h;
}

void ofxMSAInteractiveObject::setPosAndSize(float _x, float _y, float _w, float _h) {
	setPos(_x, _y);
	setSize(_w, _h);
}

bool ofxMSAInteractiveObject::isMouseOver() {
	return _mouseOver;
}

bool ofxMSAInteractiveObject::isMouseDown() {
	return _mouseDown;
}

int ofxMSAInteractiveObject::getMouseX() {
	return _mouseX;
}

int ofxMSAInteractiveObject::getMouseY() {
	return _mouseY;
}

int ofxMSAInteractiveObject::getLastMouseButton() {
	return _mouseButton;
}

bool ofxMSAInteractiveObject::hitTest(int tx, int ty) {
	return ((tx > x) && (tx < x + width) && (ty > y) && (ty < y + height));
}



void ofxMSAInteractiveObject::_setup(ofEventArgs &e) {
	if(!enabled) return;
	setup();
}

void ofxMSAInteractiveObject::_update(ofEventArgs &e) {
	if(!enabled) return;
	
	// check to see if object has moved, and if so update mouse events
	if(oldRect.x != this->x || oldRect.y != this->y || oldRect.width != this->width ||oldRect.height != this->height) {
		ofMouseEventArgs e;
		e.button = _mouseButton;
		e.x = _mouseX;
		e.y = _mouseY;
		if(_mouseDown) _mouseDragged(e);	
		else _mouseMoved(e);
		
		oldRect =  (ofRectangle) (*this);
	}
	update();
}

void ofxMSAInteractiveObject::_draw(ofEventArgs &e) {
	if(!enabled) return;
	draw();
}

void ofxMSAInteractiveObject::_exit(ofEventArgs &e) {
	if(!enabled) return;
	exit();
}


void ofxMSAInteractiveObject::_mouseMoved(ofMouseEventArgs &e) {
	int x = e.x;
	int y = e.y;
	int button = e.button;
	if(verbose) printf("ofxMSAInteractiveObject::_mouseMoved(x: %i, y: %i)\n", x, y);
	if(!enabled) return;
	
	_mouseX = x;
	_mouseY = y;
	
	if(hitTest(x, y)) {						// if mouse is over the object
		if(!_mouseOver) {						// if wasn't over previous frame
			onRollOver(x, y);						// call onRollOver
			_mouseOver = true;						// update flag
		}
		onMouseMove(x, y);						// and trigger onMouseMove
	} else if(_mouseOver) {					// if mouse is not over the object, but the flag is true (From previous frame)
		onRollOut();							// call onRollOut
		_mouseOver = false;						// update flag
	}
}


void ofxMSAInteractiveObject::_mousePressed(ofMouseEventArgs &e) {
	int x = e.x;
	int y = e.y;
	int button = e.button;
	
	if(verbose) printf("ofxMSAInteractiveObject::_mousePressed(x: %i, y: %i, button: %i)\n", x, y, button);
	if(!enabled) return;

	_mouseX = x;
	_mouseY = y;
	_mouseButton = button;
	
	if(hitTest(x, y)) {						// if mouse is over
		if(!_mouseDown) {						 // if wasn't down previous frame
			onPress(x, y, button);					// call onPress
			_mouseDown = true;						// update flag
		}
	} else {								// if mouse is not over
		onPressOutside(x, y, button);
	}
}

void ofxMSAInteractiveObject::_mouseDragged(ofMouseEventArgs &e) {
	int x = e.x;
	int y = e.y;
	int button = e.button;
	
	if(verbose) printf("ofxMSAInteractiveObject::_mouseDragged(x: %i, y: %i, button: %i)\n", x, y, button);
	if(!enabled) return;

	_mouseX = x;
	_mouseY = y;
	_mouseButton = button;

	if(hitTest(x, y)) {						// if mouse is over the object
		if(!_mouseOver) {						// if wasn't over previous frame
			//				onPress(x, y);							// call onPress - maybe not
			_mouseOver = true;						// update flag
		}
		onDragOver(x, y, button);				// and trigger onDragOver
	} else {
		if(_mouseOver) {					// if mouse is not over the object, but the flag is true (From previous frame)
			onRollOut();							// call onRollOut
			_mouseOver = false;						// update flag
		}
		if(_mouseDown) {
			onDragOutside(x, y, button);
		}
	}
}

void ofxMSAInteractiveObject::_mouseReleased(ofMouseEventArgs &e) {
	int x = e.x;
	int y = e.y;
	int button = e.button;
	
	if(verbose) printf("ofxMSAInteractiveObject::_mouseReleased(x: %i, y: %i, button: %i)\n", x, y, button);
	if(!enabled) return;

	_mouseX = x;
	_mouseY = y;
	_mouseButton = button;
	
	if(hitTest(x, y)) {
		onRelease(x, y, button);
	} else {
		if(_mouseDown) onReleaseOutside(x, y, button);
	}
	_mouseDown = false;
}


void ofxMSAInteractiveObject::_keyPressed(ofKeyEventArgs &e) {
	int key = e.key;
	if(verbose) printf("ofxMSAInteractiveObject::_keyPressed(key: %i)\n", key);
	if(!enabled) return;
	keyPressed(key);
}


void ofxMSAInteractiveObject::_keyReleased(ofKeyEventArgs &e) {
	int key = e.key;	
	if(verbose) printf("ofxMSAInteractiveObject::_keyReleased(key: %i)\n", key);
	if(!enabled) return;
	keyReleased(key);
}
