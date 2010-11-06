

#pragma once
#include "ofMain.h"
#include "ofxBox2dBaseShape.h"

class ofxBox2dCircle : public ofxBox2dBaseShape {
	
public:
	
	b2CircleDef circle;
	//------------------------------------------------
	
	ofxBox2dCircle() {
	}
	
	//------------------------------------------------
	void setup(b2World * b2dworld, float x, float y, float size, bool isFixed=false) {
		
		if(b2dworld == NULL) {
			ofLog(OF_LOG_NOTICE, "- must have a valid world -");
			return;
		}
		
		world				= b2dworld;
		circle.radius		= size/OFX_BOX2D_SCALE;
		bIsFixed			= isFixed;
		
		if(isFixed) {
			circle.density		= 0;
			circle.restitution  = 0;
			circle.friction		= 0;
		}
		else {
			circle.density		= mass;
			circle.restitution  = bounce;
			circle.friction		= friction;
		}
		bodyDef.position.Set(x/OFX_BOX2D_SCALE, y/OFX_BOX2D_SCALE);	
		
		body = world->CreateBody(&bodyDef);
		if(body) {
			body->SetLinearVelocity(b2Vec2(0.0, 0.0));
			body->CreateShape(&circle);
			body->SetMassFromShapes();
		}
		// anything that you need called
		init();
	}
	
	//------------------------------------------------
	float getRadius() {
		if(body != NULL) {
			b2Shape* shape		= body->GetShapeList();
			b2CircleShape *data = (b2CircleShape*)shape;
			return data->GetRadius() * OFX_BOX2D_SCALE;
		}
	}
	
	
	//------------------------------------------------
	float getRotation() {
		if(body != NULL) {
			const  b2XForm& xf	= body->GetXForm();
			float  r			= getRadius()/OFX_BOX2D_SCALE;
			b2Vec2 a			= xf.R.col1;
			b2Vec2 p1			= body->GetPosition();
			b2Vec2 p2			= p1 + r * a;
			
			float dx = p2.x+r/2 - p1.x+r/2;
			float dy = p2.y - p1.y;
			return ofRadToDeg(atan2(dy, dx));
		}
	}
	
	//------------------------------------------------ 
	void disableCollistion() {
		if(body != NULL) {
			circle.filter.maskBits = 0x0;		
		}
	}
	
	//------------------------------------------------
	/*
	 Im not sure about this it seems like a bad idea.
	 I cant figure out another way to change the radius of
	 a shape that we have
	 
	 -- any help here :) --
	 
	 */
	void setRadius(float r) {
		if(body != NULL) {
			for(b2Shape* s=body->GetShapeList(); s; s=s->GetNext()) {
				body->DestroyShape(s);
			}
			
			circle.radius	    = r/OFX_BOX2D_SCALE;
			circle.density		= mass;
			circle.restitution  = bounce;
			circle.friction		= friction;
			
			//body = world->CreateBody(&bodyDef);
			body->SetLinearVelocity(b2Vec2(0.0, 0.0));
			body->CreateShape(&circle);
			body->SetMassFromShapes();
		}
	}
	
	//------------------------------------------------
	virtual void draw() {
		
		if(dead && body == NULL) return;
		
		float radius = getRadius();
		
		glPushMatrix();
		glTranslatef(getPosition().x, getPosition().y, 0);
		
		if(bIsFixed) {
			ofSetColor(255, 0, 255);
			ofFill();
			ofCircle(0, 0, radius);	
		}
		else {
			ofSetColor(0, 255, 255);
			ofNoFill();
			ofCircle(0, 0, radius);
			
			ofSetColor(255, 0, 255);
			ofFill();
			ofCircle(0, 0, radius/10.0);
			
			ofSetColor(255, 255, 255);
			ofNoFill();
			ofCircle(0, 0, radius/5.0);
		}
		
		glPopMatrix();
		
		float angle			= getRotation();
		const b2XForm& xf	= body->GetXForm();
		b2Vec2	center		= body->GetPosition();
		b2Vec2	axis		= xf.R.col1;
		b2Vec2	p			= center + radius/OFX_BOX2D_SCALE * axis;
		
		ofSetColor(0xff00ff);
		ofLine(getPosition().x, getPosition().y, p.x*OFX_BOX2D_SCALE, p.y*OFX_BOX2D_SCALE);
		
	}
	
};














