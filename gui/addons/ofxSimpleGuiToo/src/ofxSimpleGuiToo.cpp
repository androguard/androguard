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

#include "ofxSimpleGuiToo.h"

ofxSimpleGuiToo gui;


//------------------------------------------------------------------------------ constrcutor
ofxSimpleGuiToo::ofxSimpleGuiToo() {
	config = NULL;
	doDefaultKeys = false;
}

void ofxSimpleGuiToo::setup() {
	config			= &defaultSimpleGuiConfig;

	doSave			= false;
	changePage		= false;
	titleButton		= NULL;

	headerPage		= &addPage("Header");
	headerPage->height = config->buttonHeight * 2;
	headerPage->width = 0;
	titleButton = &headerPage->addButton("title", changePage);
	headerPage->addToggle("Auto Save", doAutoSave);
	headerPage->addButton("Save Settings", doSave);
	headerPage->addFPSCounter();

	addPage();
	setAutoSave(true);
	setAlignRight(false);
	setDraw(false);
	setPage(1);
	
	ofAddListener(ofEvents.keyPressed, this, &ofxSimpleGuiToo::keyPressed);
}



void ofxSimpleGuiToo::addListeners() {
//	ofAddListener(ofEvents.setup, this, &ofxSimpleGuiToo::setup);
	ofAddListener(ofEvents.update, this, &ofxSimpleGuiToo::update);
//	ofAddListener(ofEvents.draw, this, &ofxSimpleGuiToo::draw);
//	ofAddListener(ofEvents.exit, this, &ofxSimpleGuiToo::exit);

	ofAddListener(ofEvents.mousePressed, this, &ofxSimpleGuiToo::mousePressed);
	ofAddListener(ofEvents.mouseMoved, this, &ofxSimpleGuiToo::mouseMoved);
	ofAddListener(ofEvents.mouseDragged, this, &ofxSimpleGuiToo::mouseDragged);
	ofAddListener(ofEvents.mouseReleased, this, &ofxSimpleGuiToo::mouseReleased);

//	ofAddListener(ofEvents.keyPressed, this, &ofxSimpleGuiToo::keyPressed);
	ofAddListener(ofEvents.keyReleased, this, &ofxSimpleGuiToo::keyReleased);
}


void ofxSimpleGuiToo::removeListeners() {
//	ofRemoveListener(ofEvents.setup, this, &ofxSimpleGuiToo::setup);
	ofRemoveListener(ofEvents.update, this, &ofxSimpleGuiToo::update);
//	ofRemoveListener(ofEvents.draw, this, &ofxSimpleGuiToo::draw);
//	ofRemoveListener(ofEvents.exit, this, &ofxSimpleGuiToo::exit);

	ofRemoveListener(ofEvents.mousePressed, this, &ofxSimpleGuiToo::mousePressed);
	ofRemoveListener(ofEvents.mouseMoved, this, &ofxSimpleGuiToo::mouseMoved);
	ofRemoveListener(ofEvents.mouseDragged, this, &ofxSimpleGuiToo::mouseDragged);
	ofRemoveListener(ofEvents.mouseReleased, this, &ofxSimpleGuiToo::mouseReleased);

//	ofRemoveListener(ofEvents.keyPressed, this, &ofxSimpleGuiToo::keyPressed);
	ofRemoveListener(ofEvents.keyReleased, this, &ofxSimpleGuiToo::keyReleased);
}

void ofxSimpleGuiToo::setDraw(bool b) {
	if(doDraw != b) {
		doDraw = b;
		if(doDraw) addListeners();
		else removeListeners();
		if(doAutoSave) saveToXML();
	}
}

void ofxSimpleGuiToo::show() {
	setDraw(true);
}

void ofxSimpleGuiToo::hide() {
	setDraw(false);
}

void ofxSimpleGuiToo::toggleDraw() {
	setDraw(!doDraw);
}

bool ofxSimpleGuiToo::isOn() {
	return doDraw;
}


void ofxSimpleGuiToo::setAutoSave(bool b) {
	doAutoSave = b;
}


void ofxSimpleGuiToo::loadFromXML() {
	ofLog(OF_LOG_VERBOSE, "ofxSimpleGuiToo::loadFromXML");// + file);

	for(int i=1; i < pages.size(); i++) {
		pages[i]->loadFromXML();
	}

	setPage(1);
}


void ofxSimpleGuiToo::saveToXML() {
	doSave = false;

	for(int i=1; i < pages.size(); i++) {
		pages[i]->saveToXML();
	}

	ofLog(OF_LOG_VERBOSE, "ofxSimpleGuiToo::saveToXML");
}


void ofxSimpleGuiToo::setAlignRight(bool b) {
	alignRight = b;
}

void ofxSimpleGuiToo::setDefaultKeys(bool b) {
	doDefaultKeys = b;
}


void ofxSimpleGuiToo::drawFocus(float x, float y) {
	glPushMatrix();
	glTranslatef(x, y, 0);
	ofFill();
//	ofSetColor(config->focusColor.r, config->focusColor.g, config->focusColor.b, 200);
	ofRect(0, 0, 10, 10);
	glPopMatrix();
}


void ofxSimpleGuiToo::draw() {
	if(!doDraw) return;
	
	ofPushStyle();
	
	glDisable(GL_DEPTH_TEST);
	
	ofSetLineWidth(3);

	glDisableClientState(GL_COLOR_ARRAY);

	headerPage->draw(0, 0, alignRight);		// this is the header
	ofSetColor(config->borderColor);
	if(alignRight) ofLine(ofGetWidth() - headerPage->width, headerPage->height, headerPage->width, headerPage->height);
	else ofLine(0, headerPage->height, headerPage->width, headerPage->height);
	pages[currentPageIndex]->draw(0.0f, headerPage->height, alignRight);
	
	ofPopStyle();
}


void ofxSimpleGuiToo::nextPage() {
	setPage(currentPageIndex + 1);
}
void ofxSimpleGuiToo::prevPage() {
	setPage(currentPageIndex - 1);
}

void ofxSimpleGuiToo::nextPageWithBlank() {
	if(doDraw) {
		setPage(currentPageIndex + 1);
		if(currentPageIndex == 1) setDraw(false);
	} else {
		setDraw(true);
		setPage(1);
	}
}



void ofxSimpleGuiToo::setPage(int i) {
	currentPageIndex = i;
	if(currentPageIndex >= pages.size()) currentPageIndex = 1;
	else if(currentPageIndex < 1) currentPageIndex = pages.size()-1;
	
	if(titleButton) titleButton->setName(ofToString(currentPageIndex) + ": " + pages[currentPageIndex]->name);
}


void ofxSimpleGuiToo::setPage(string name) {
//	ofxSimpleGuiPage *page;
	for(int i=1; i < pages.size(); i++) {
		if(name.compare(pages[i]->name) == 0) {
			setPage(i);
			break;
		}
	}
}


ofxSimpleGuiPage& ofxSimpleGuiToo::page(int i) {
	return *pages.at(i);
}

ofxSimpleGuiPage& ofxSimpleGuiToo::page(string name) {
	if(!config) setup();
	for(int i=1; i<pages.size(); i++) if(name.compare(pages[i]->name) == 0) return *pages[i];
}


ofxSimpleGuiPage& ofxSimpleGuiToo::currentPage() {
	return page(currentPageIndex);
}

vector <ofxSimpleGuiPage*>&	ofxSimpleGuiToo::getPages() {
	return pages;
}



ofxSimpleGuiPage &ofxSimpleGuiToo::addPage(string name) {
	if(!config) setup();

	ofxSimpleGuiPage *newPage = new ofxSimpleGuiPage(name);//ofToString(pages.size(), 0) + ": " + name);
	pages.push_back(newPage);
	if(name == "") newPage->setName("SETTINGS");
	static bool b;
//	if(pages.size() > 1) headerPage->addTitle(newPage->name);		// if this isn't the first page, add to header
//	if(pages.size() > 1) newPage->addTitle(newPage->name);		// if this isn't the first page, add to header
	setPage(pages.size() - 1);
	return *newPage;
}

ofxSimpleGuiControl &ofxSimpleGuiToo::control(string name) {
	for(int i = 0; i < pages.size(); i++) {
		for(int j = 0; j < pages[i]->getControls().size(); j++) {
			if(name==pages[i]->getControls()[j]->name) {
				return *pages[i]->getControls()[j];
			}
		}
	}
//	return NULL;
}


ofxSimpleGuiControl &ofxSimpleGuiToo::addControl(ofxSimpleGuiControl& control) {
	if(!config) setup();
	return pages[currentPageIndex]->addControl(control);
}

ofxSimpleGuiButton &ofxSimpleGuiToo::addButton(string name, bool &value) {
	if(!config) setup();
	return pages[currentPageIndex]->addButton(name, value);
}

ofxSimpleGuiContent &ofxSimpleGuiToo::addContent(string name, ofBaseDraws &content, float fixwidth) {
	if(!config) setup();
	return pages[currentPageIndex]->addContent(name, content, fixwidth);
}

ofxSimpleGuiFPSCounter &ofxSimpleGuiToo::addFPSCounter() {
	if(!config) setup();
	return pages[currentPageIndex]->addFPSCounter();
}

ofxSimpleGuiQuadWarp &ofxSimpleGuiToo::addQuadWarper(string name, ofBaseDraws &baseDraw, ofPoint *pts) {
	return pages[currentPageIndex]->addQuadWarper(name, baseDraw, pts);
}
//
//ofxSimpleGuiMovieSlider &ofxSimpleGuiToo::addMovieSlider(string name, ofVideoPlayer& input) {
//	return pages[currentPageIndex]->addMovieSlider(name, input);
//}

ofxSimpleGuiSliderInt &ofxSimpleGuiToo::addSlider(string name, int &value, int min, int max) {
	if(!config) setup();
	return pages[currentPageIndex]->addSlider(name, value, min, max);
}

ofxSimpleGuiSliderFloat &ofxSimpleGuiToo::addSlider(string name, float &value, float min, float max) {
	if(!config) setup();
	return pages[currentPageIndex]->addSlider(name, value, min, max);
}

ofxSimpleGuiSlider2d &ofxSimpleGuiToo::addSlider2d(string name, ofPoint& value, float xmin, float xmax, float ymin, float ymax) {
	if(!config) setup();
	return pages[currentPageIndex]->addSlider2d(name, value, xmin, xmax, ymin, ymax);
}

ofxSimpleGuiTitle &ofxSimpleGuiToo::addTitle(string name, float height) {
	if(!config) setup();
	return pages[currentPageIndex]->addTitle(name, height);
}

ofxSimpleGuiToggle &ofxSimpleGuiToo::addToggle(string name, bool &value) {
	if(!config) setup();
	return pages[currentPageIndex]->addToggle(name, value);
}


ofxSimpleGuiColorPicker &ofxSimpleGuiToo::addColorPicker(string name, float *values) {
	if(!config) setup();
	return pages[currentPageIndex]->addColorPicker(name, values);
}


ofxSimpleGuiComboBox &ofxSimpleGuiToo::addComboBox(string name, int &value, int numChoices, string* choiceTitles)  {
	if(!config) setup();
	return pages[currentPageIndex]->addComboBox(name, value, numChoices, choiceTitles);
}


//void ofxSimpleGuiToo::setup(ofEventArgs &e) {
void ofxSimpleGuiToo::update(ofEventArgs &e) {
	if(changePage) {
		nextPage();
		changePage = false;
	}

	headerPage->update(e);
	pages[currentPageIndex]->height = ofGetHeight();
	pages[currentPageIndex]->update(e);


//	if(doSaveBackup) doSave = true;

	if(doSave) saveToXML();
}
//void ofxSimpleGuiToo::draw(ofEventArgs &e) {
//void ofxSimpleGuiToo::exit(ofEventArgs &e) {

void ofxSimpleGuiToo::mouseMoved(ofMouseEventArgs &e) {
	headerPage->mouseMoved(e);
	pages[currentPageIndex]->mouseMoved(e);
}

void ofxSimpleGuiToo::mousePressed(ofMouseEventArgs &e) {
	headerPage->mousePressed(e);
	pages[currentPageIndex]->mousePressed(e);
}

void ofxSimpleGuiToo::mouseDragged(ofMouseEventArgs &e) {
	headerPage->mouseDragged(e);
	pages[currentPageIndex]->mouseDragged(e);
}

void ofxSimpleGuiToo::mouseReleased(ofMouseEventArgs &e) {
	headerPage->mouseReleased(e);
	pages[currentPageIndex]->mouseReleased(e);
//	if(doAutoSave) doSave = true;
	if(doAutoSave) saveToXML();
}

void ofxSimpleGuiToo::keyPressed(ofKeyEventArgs &e) {
	if(doDefaultKeys) {
		if(e.key == ' ') {
			toggleDraw();
		} else if(e.key>='0' && e.key<='9') {
			setPage((int)(e.key - '0'));
			setDraw(true);
		} else if(doDraw) {
			switch(e.key) {
				case '[': prevPage(); break;
				case ']': nextPage(); break;
			}
		}
	}
	
	if(doDraw) {
		headerPage->keyPressed(e);
		pages[currentPageIndex]->keyPressed(e);
	}
	
}

void ofxSimpleGuiToo::keyReleased(ofKeyEventArgs &e) {
	headerPage->keyReleased(e);
	pages[currentPageIndex]->keyReleased(e);
}

/*
//------------------------------------------------------------------------ mouse moved
void ofxSimpleGuiToo::mouseMoved(int x, int y) {
	mx = x; my = y;
}

//------------------------------------------------------------------------ mouse released
void ofxSimpleGuiToo::mouseReleased() {
	if(doAutoSave) {
		saveToXML();
	}
}

//------------------------------------------------------------------------ key released
void ofxSimpleGuiToo::keyReleased(int key) {
	if(doAutoSave) {
		saveToXML();
	}
}

//------------------------------------------------------------------------ key press
void ofxSimpleGuiToo::keyPressed(int key) {

}
*/

