
#pragma once
#include "ofMain.h"
#include "Box2D.h"
#include "ofxBox2dUtils.h"

class ofxBox2dBaseShape {
	
public:
	
	b2World*	world;
	b2BodyDef	bodyDef;
	b2Body*		body;
	
	bool		dead;
	bool		alive;
	bool		bIsFixed;
	
	float		mass;
	float		bounce;
	float		friction;
	
	ofxBox2dBaseShape() {
		
		dead  = false;
		alive = false;
		bIsFixed = false;
		
		world = NULL;
		body  = NULL;
		
		mass     = 0.0;
		bounce   = 0.0;
		friction = 0.0;
		bodyDef.allowSleep = true;
	}		
	
	//------------------------------------------------ 
	~ofxBox2dBaseShape() {
		if(alive) destroyShape();
	}
	
	//------------------------------------------------ 
	virtual void init() {
	}
	
	//------------------------------------------------ 
	virtual void setElasticity(float val) {
		bounce = val;
	}
	
	virtual void setPhysics(float m, float bnc, float frc) {
		mass = m; bounce = bnc; friction = frc;
	}
	
	//------------------------------------------------ 
	virtual void setMass(float val) {
		// -- this is not working ! --
		/*b2MassData data;
		 data.mass = 3;
		 data.center = body->GetPosition();
		 data.I = body->GetInertia();
		 body->SetMass(&data);
		 */
	}

	//------------------------------------------------ 
	void setData(void*data) {
		if(body) {
			body->SetUserData(data);
		}
		else {
			ofLog(OF_LOG_NOTICE, "- must have a valid body -");
		}
	}
	
	//------------------------------------------------ 
	void* getData() {
		if(body) {
			body->GetUserData();
		}
		else {
			ofLog(OF_LOG_NOTICE, "- must have a valid body -");
		}
	}
	
	//------------------------------------------------ 
	virtual void setFilterData(b2FilterData data) {
		for(b2Shape* s=body->GetShapeList(); s; s=s->GetNext()) {
			
			//b2FilterData filter = s->GetFilterData();
			//			filter.groupIndex = newValue;
			//			myShape->SetFilterData(filter):
			//			myWorld->Refilter(myShape);
			
			s->SetFilterData(data);
			world->Refilter(s);
		}
		
	}
	
	//------------------------------------------------ 
	virtual void setRotationFriction(float f) {
		bodyDef.angularDamping = f;
	}
	
	//------------------------------------------------ 
	virtual void setDamping(float f) {
		body->SetLinearDamping(f);
	}
	
	//------------------------------------------------ 
	virtual void enableGravity(bool b) {
		bodyDef.isGravitated = b;
	}
	
	//------------------------------------------------ 
	virtual void setFixedRotation(bool b) {
		bodyDef.fixedRotation = b;
	}
	
	//------------------------------------------------ 
	virtual void setWorld(b2World * theworld) {
		if(theworld == NULL) {
			ofLog(OF_LOG_NOTICE, "- must have a valid world -");
			return;
		}
		world = theworld;
	}
	//------------------------------------------------ 
	virtual void setPosition(float x, float y) {
		body->SetXForm(b2Vec2(b2dNum(x), b2dNum(y)), 0);
		body->WakeUp();
	}
	virtual void setPosition(ofPoint p) {
		setPosition(p.x, p.y);
	}
	
	//------------------------------------------------ 
	virtual void setVelocity(float x, float y) {
		if(body != NULL) {
			body->SetLinearVelocity(b2Vec2(x, y));
		}
	}
	virtual void setVelocity(ofPoint p) {
		setVelocity(p.x, p.y);
	}
	ofPoint getVelocity() {
		return ofPoint(body->GetLinearVelocity().x, body->GetLinearVelocity().y);
	}
	
	//------------------------------------------------ 
	virtual void addDamping(float fx, float fy) {
		if(body != NULL) {
			b2Vec2 v = body->GetLinearVelocity();
			v.x *= fx;	v.y *= fy;
			body->SetLinearVelocity(v);
		}
	}
	virtual void addDamping(float f) {
		addDamping(f, f);
	}
	
	
	//------------------------------------------------
	virtual void addForce(ofPoint pt, ofPoint amt) {
		if(body != NULL) {
			body->ApplyForce(b2Vec2(pt.x/OFX_BOX2D_SCALE, pt.y/OFX_BOX2D_SCALE), b2Vec2(amt.x, amt.y));
		}
	}
	
	//------------------------------------------------
	virtual void addImpulseForce(ofPoint pt, ofPoint amt=1.0) {
		if(body != NULL) {
			body->ApplyImpulse(b2Vec2(pt.x/OFX_BOX2D_SCALE, pt.y/OFX_BOX2D_SCALE), b2Vec2(amt.x, amt.y));
		}
	}
	
	//------------------------------------------------
	virtual void addAttractionPoint(ofPoint pt, float amt, float minDis=NULL) {
		
		// if(minDis == NULL) minDis = 1; // not using this
		
		if(body != NULL) {
			b2Vec2 P(pt.x/OFX_BOX2D_SCALE, pt.y/OFX_BOX2D_SCALE);
			b2Vec2 D = P - body->GetPosition(); 
			
			P.Normalize();
			b2Vec2 F = amt * D;
			body->ApplyForce(F, P);
		}
	}
	
	//------------------------------------------------
	virtual void addRepulsionForce(ofPoint pt, float radius, float amt) {
		/*if(body != NULL) {
			b2Vec2 P(pt.x/OFX_BOX2D_SCALE, pt.y/OFX_BOX2D_SCALE);
			b2Vec2 D = P - body->GetPosition(); 
			if(D.LengthSquared() < minDis) {;
				P.Normalize();
				b2Vec2 F = amt * D;
				body->ApplyForce(F, P);
			}
		}*/
		
		if(body != NULL) {
			b2Vec2 P(pt.x/OFX_BOX2D_SCALE, pt.y/OFX_BOX2D_SCALE);
			b2Vec2 D = P - body->GetPosition(); 
			if(D.LengthSquared() < radius) {;
				P.Normalize();
				b2Vec2 F = amt * D;
				body->ApplyForce(-F, P);
			}
		}
	}
	
	virtual void addAttractionPoint(float x, float y, float amt, float minDis=NULL) {
		addAttractionPoint(ofPoint(x, y), amt, minDis);
	}
	
	//------------------------------------------------ 
	virtual void moveTo(float x, float y) {
		
		setPosition(x, y);	
		//printf("%f\n", body->GetLinearVelocity().x);
	}
	
	//------------------------------------------------ 
	ofPoint getPosition() {
		ofPoint p;
		if(body != NULL) {
			p.set(body->GetPosition().x, body->GetPosition().y);
			p*=OFX_BOX2D_SCALE;
		}
		return p;
	}
	
	//------------------------------------------------
	ofPoint getB2DPosition() {
		return getPosition()/OFX_BOX2D_SCALE;
	}
	
	//------------------------------------------------
	virtual void destroyShape() {
		
		if(world == NULL) {
			ofLog(OF_LOG_NOTICE, "- must have a valid world -");
			return;
		}
		else if(!body) {
			ofLog(OF_LOG_NOTICE, "- null body -");
			return;
		}			
		else if(dead) {
			ofLog(OF_LOG_NOTICE, "- already dead -");
			return;
		}
		
		for(b2Shape* s=body->GetShapeList(); s; s=s->GetNext()) {
			body->DestroyShape(s);
		}
		
		world->DestroyBody(body);
		body  = NULL;
		dead  = true;
		alive = false;
		
		//printf("--- dead ---\n");
	}
	
	//------------------------------------------------
	virtual void update() { }
	virtual void draw() { }
	
};