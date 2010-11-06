#include "./include/appController.h"

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

    box2d.init();
    box2d.setGravity(0, 10);
    box2d.createFloor();
    box2d.checkBounds(true);
    box2d.setFPS(30.0);

        // lets draw a simple lanscape
        ofPoint p(40, 400);
        int segs = 50;
        lineStrip.setWorld(box2d.getWorld());
        lineStrip.clear();
        for(int i=0; i<segs; i++) {
                p.x += 15;
                lineStrip.addPoint(p.x, p.y+sin(i*ofRandom(0.01, 0.5))*30);
        }
        lineStrip.createShape();

    gui.addTitle("A group");

  //  gui.loadFromXML();
    gui.show();
}

void appController::mainLoop(){
    box2d.update();
}

void appController::draw(){
    for(int i=0; i<circles.size(); i++) {
        circles[i].draw();
    }

    lineStrip.draw();

    box2d.draw();
    gui.draw();
}

void appController::keyPressed(int key){
    if(key == 'c') {
                float r = ofRandom(4, 20);              // a random radius 4px - 20px
                ofxBox2dCircle circle;
                circle.setPhysics(3.0, 0.53, 0.1);
                circle.setup(box2d.getWorld(),100,100,r);// mouseX, mouseY, r);
                circles.push_back(circle);
        }

}
