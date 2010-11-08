#include "appController.h"

appController::appController()
{
    //ctor
}

appController::~appController()
{
    //dtor
}

void appController::setup(){
    ofBackground(0, 0, 0);
    ofSetVerticalSync(true);

    gui.addTitle("A group");

  //  gui.loadFromXML();
    gui.show();
}

void appController::mainLoop(){
}

void appController::draw(){
    ofNoFill();
    ofRect(200,600,40,60);

    gui.draw();
}

void appController::keyPressed(int key){

}
