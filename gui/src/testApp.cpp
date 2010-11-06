#include "testApp.h"

//--------------------------------------------------------------
void testApp::setup(){
    ofBackground(255,255,255);
    ofSetWindowTitle("Androgui");

    appCtrl.setup();
}

//--------------------------------------------------------------
void testApp::update(){
  appCtrl.mainLoop();
}

//--------------------------------------------------------------
void testApp::draw(){
    ofSetupScreen();
    appCtrl.draw();
}

//--------------------------------------------------------------
void testApp::keyPressed(int key){
    appCtrl.keyPressed(key);
}

//--------------------------------------------------------------
void testApp::keyReleased(int key){

}

//--------------------------------------------------------------
void testApp::mouseMoved(int x, int y ){

}

//--------------------------------------------------------------
void testApp::mouseDragged(int x, int y, int button){

}

//--------------------------------------------------------------
void testApp::mousePressed(int x, int y, int button){

}

//--------------------------------------------------------------
void testApp::mouseReleased(int x, int y, int button){

}

//--------------------------------------------------------------
void testApp::windowResized(int w, int h){

}

