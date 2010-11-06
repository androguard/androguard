#pragma once


class ofxBox2dJoint {
	
public:
	
	b2World * world;
	b2Joint * joint;
	bool alive;
	
	ofxBox2dJoint() {
		world = NULL;
		alive = false;
	}
	
	void setWorld(b2World * w) {
		if(w == NULL) {
			ofLog(OF_LOG_NOTICE, "- box2d world needed -");	
			return;
		}
		world = w;
		alive = true;
	}
	
	void destroyJoint() {
		world->DestroyJoint(joint);
		joint = NULL;
	}
	
	void addJoint(b2Body * a, b2Body * b, float stiffness=3.0f, float damping=0.6f ) {
		
		if(world == NULL) {
			ofLog(OF_LOG_NOTICE, "- no joint added - box2d world needed -");	
			return;
		}
		
		b2DistanceJointDef jd;
		b2Vec2 p1, p2, d;
		
		jd.frequencyHz  = stiffness;
		jd.dampingRatio = damping;
		
		jd.body1 = a;
		jd.body2 = b;
		
		jd.localAnchor1.Set(0, 0);
		jd.localAnchor2.Set(0, 0);
		jd.collideConnected = false;
		
		p1 = jd.body1->GetWorldPoint(jd.localAnchor1);
		p2 = jd.body2->GetWorldPoint(jd.localAnchor2);
		d = p2 - p1;
		jd.length = d.Length();
		
		joint = world->CreateJoint(&jd);
	}
	
	void draw(int alpha=200) {
		
		if(!alive) return;
		
		ofEnableAlphaBlending();
		ofSetColor(255, 0, 255, alpha);
		
		b2Vec2 p1 = joint->GetAnchor1();
		b2Vec2 p2 = joint->GetAnchor2();
		
		p1 *= OFX_BOX2D_SCALE;
		p2 *= OFX_BOX2D_SCALE;
		ofLine(p1.x, p1.y, p2.x, p2.y);	   
		ofDisableAlphaBlending();
	}
};












