#pragma once
#include "ofMain.h"
#include "ofxBox2dBaseShape.h"

class ofxBox2dPolygon : public ofxBox2dBaseShape {
	
public:
	
	ofPoint				centroid;
	b2PolygonDef		poly;
	int					vertexCount;
	vector	<ofPoint>	vertices;
	
	//------------------------------------------------
	ofxBox2dPolygon() {
	}
	
	//------------------------------------------------ 
	void addVertex(float x, float y) {
		vertices.push_back(ofPoint(x, y));
	}
	void addVertex(ofPoint pt) {
		vertices.push_back(pt);
	}
	
	//------------------------------------------------
	ofPoint getPosition() {
	}
	
	//------------------------------------------------
	float getArea() {
		int i, j, n = vertices.size();
		float area = 0;
		
		for (i = 0; i < n; i++) {
			j = (i + 1) % n;
			area += vertices[i].x * vertices[j].y;
			area -= vertices[j].x * vertices[i].y;
		}
		area /= 2.0;
		return (area);
	}
	
	
	//------------------------------------------------
	ofPoint getCenter() {
		float cx = 0, cy = 0;
		float area = getArea();
		int i, j, n = vertices.size();
		
		float factor = 0;
		for (i = 0; i < n; i++) {
			j = (i + 1) % n;
			factor = (vertices[i].x * vertices[j].y
					- vertices[j].x * vertices[i].y);
			cx += (vertices[i].x + vertices[j].x) * factor;
			cy += (vertices[i].y + vertices[j].y) * factor;
		}
		area *= 6.0f;
		factor = 1 / area;
		cx *= factor;
		cy *= factor;
		ofPoint pt(cx, cy);
		return pt;
	}		
	
	//------------------------------------------------
	void update() {
		
		// update the position of the verticies
		for(b2Shape* s=body->GetShapeList(); s; s=s->GetNext()) {
			const b2XForm&	xf		= body->GetXForm();		
			b2PolygonShape* poly	= (b2PolygonShape*)s;
			int				count	= poly->GetVertexCount();
			const b2Vec2*	verts	= poly->GetVertices();
			if(count == vertices.size()) {
				for(int j=0; j<count; j++) {
					b2Vec2 pt = b2Mul(xf, verts[j]);
					vertices[j].x = pt.x*OFX_BOX2D_SCALE;
					vertices[j].y = pt.y*OFX_BOX2D_SCALE;
				}
			}
		}	
	}
	//------------------------------------------------
	b2Vec2 computeCentroid(const b2Vec2* vs, int32 count) {
		
		//b2Assert(count >= 3);
		
		b2Vec2 c; c.Set(0.0f, 0.0f);
		float32 area = 0.0f;
		
		// pRef is the reference point for forming triangles.
		// It's location doesn't change the result (except for rounding error).
		b2Vec2 pRef(0.0f, 0.0f);
		
		
#if 0
		// This code would put the reference point inside the polygon.
		for (int32 i = 0; i < count; ++i)
		{
			pRef += vs[i];
		}
		pRef *= 1.0f / count;
#endif
		
		
		const float32 inv3 = 1.0f / 3.0f;
		
		for(int32 i=0; i<count; ++i) {
			
			// Triangle vertices.
			b2Vec2 p1 = pRef;
			b2Vec2 p2 = vs[i];
			b2Vec2 p3 = i + 1 < count ? vs[i+1] : vs[0];
			
			b2Vec2 e1 = p2 - p1;
			b2Vec2 e2 = p3 - p1;
			
			float32 D = b2Cross(e1, e2);
			
			float32 triangleArea = 0.5f * D;
			area += triangleArea;
			
			// Area weighted centroid
			c += triangleArea * inv3 * (p1 + p2 + p3);
		}
		
		// Centroid
		//b2Assert(area > B2_FLT_EPSILON);
		c *= 1.0f / area;
		return c;
	}
	
	//------------------------------------------------
	bool validateShape() {
		
		int count = (int)vertices.size();
		b2Vec2 vertexArray[count];
		
		for(int i=0; i<count; i++) {
			vertexArray[i].Set(vertices[i].x, vertices[i].y);
		}
		b2Vec2 center = computeCentroid(vertexArray, count);
		
		// we need at least three vertices
		if(3 > count && count > b2_maxPolygonVertices) {
			return false;
		}
		
		// normals
		b2Vec2 v_normals[b2_maxPolygonVertices];
		
		for(int i=0; i<count; i++) {
			int i1 = i;
			int i2 = i + 1 < count ? i + 1 : 0;
			b2Vec2 edge = vertexArray[i2] - vertexArray[i1];
			if (edge.LengthSquared() <= B2_FLT_EPSILON * B2_FLT_EPSILON) {
				return false;
			}
			v_normals[i] = b2Cross(edge, 1.0f);
			v_normals[i].Normalize();
		}
		
		
		// Ensure the polygon is convex.
		for(int i=0; i<count; i++) {
			for(int j=0; j<count; j++) {
				// Don't check vertices on the current edge.
				if (j == i || j == (i + 1) % count) {
					continue;
				}
				
				// Your polygon is non-convex (it has an indentation).
				// Or your polygon is too skinny.
				float32 s = b2Dot(v_normals[i], vertexArray[j] - vertexArray[i]);
				if(s >= -b2_linearSlop) return false;
			}
		}
		
		// Ensure the polygon is counter-clockwise.
		for(int i=1; i<count; i++) {
			
			float32 cross = b2Cross(v_normals[i-1], v_normals[i]);
			
			// Keep asinf happy.
			cross = b2Clamp(cross, -1.0f, 1.0f);
			
			// You have consecutive edges that are almost parallel on your polygon.
			float32 angle = asinf(cross);
			if (angle <= b2_angularSlop) return false;
		}
		
		// Compute the polygon centroid.
		b2Vec2 m_centroid = computeCentroid(vertexArray, count);//ComputeCentroid(vertexArray, vertexCount);
		b2Vec2 v_coreVertices[b2_maxPolygonVertices];
		
		for(int i=0; i<count; i++) {
			
			int i1 = i - 1 >= 0 ? i - 1 : count - 1;
			int i2 = i;
			
			b2Vec2 n1 = v_normals[i1];
			b2Vec2 n2 = v_normals[i2];
			b2Vec2 v  = vertexArray[i] - m_centroid;
			
			b2Vec2 d;
			d.x = b2Dot(n1, v) - b2_toiSlop;
			d.y = b2Dot(n2, v) - b2_toiSlop;
			
			// Shifting the edge inward by b2_toiSlop should
			// not cause the plane to pass the centroid.
			//printf("--- d: %f  %f\n ---", d.x, d.y);
			
			// Your shape has a radius/extent less than b2_toiSlop.
			if (d.x < b2_toiSlop || d.y < b2_toiSlop) {
				//	printf("---BAD SHAPE d: %f  %f\n ---", d.x, d.y);
				
				return false;
			}
			
		}
		
		/*
		 // Copy the vertices and set new vertex count.
		 m_vertexCount = vertexCount;
		 
		 //There will be some kind of error checking anyway, only in the debug version
		 b2Assert(3 <= m_vertexCount && m_vertexCount <= b2_maxPolygonVertices);
		 
		 for (int i = 0; i < m_vertexCount; i++)
		 {
		 m_vertices[ i ] = vertexArray[ i ];
		 }
		 
		 // Compute normals.
		 for (int i = 0; i < m_vertexCount; i++)
		 {
		 int i1 = i;
		 int i2 = i + 1 < m_vertexCount ? i + 1 : 0;
		 b2Vec2 edge = m_vertices[i2] - m_vertices[i1];
		 b2Assert(edge.LengthSquared() > B2_FLT_EPSILON * B2_FLT_EPSILON);
		 m_normals[i] = b2Cross(edge, 1.0f);
		 m_normals[i].Normalize();
		 }
		 
		 // Compute the polygon centroid.
		 m_centroid = ComputeCentroid(m_vertices, m_vertexCount);
		 
		 // Compute the oriented bounding box.
		 ComputeOBB(&m_obb, m_vertices, m_vertexCount);
		 
		 // Create core polygon shape by shifting edges inward.
		 // Also compute the min/max radius for CCD.
		 for(int i=0; i<m_vertexCount; i++) {
		 
		 int i1 = i - 1 >= 0 ? i - 1 : m_vertexCount - 1;
		 int i2 = i;
		 
		 b2Vec2 n1 = m_normals[i1];
		 b2Vec2 n2 = m_normals[i2];
		 b2Vec2 v = m_vertices[i] - m_centroid;;
		 
		 b2Vec2 d;
		 d.x = b2Dot(n1, v) - b2_toiSlop;
		 d.y = b2Dot(n2, v) - b2_toiSlop;
		 
		 // Shifting the edge inward by b2_toiSlop should
		 // not cause the plane to pass the centroid.
		 
		 // Your shape has a radius/extent less than b2_toiSlop.
		 b2Assert(d.x >= 0.0f);
		 b2Assert(d.y >= 0.0f);
		 b2Mat22 A;
		 A.col1.x = n1.x; A.col2.x = n1.y;
		 A.col1.y = n2.x; A.col2.y = n2.y;
		 m_coreVertices[i] = A.Solve(d) + m_centroid;
		 }
		 */
		return true;
		
	}
	
	//------------------------------------------------
	void createShape(b2World * b2dworld, float x, float y) {
		
		if(b2dworld == NULL) {
			ofLog(OF_LOG_NOTICE, "- must have a valid world -");
			return;
		}
		if((int)vertices.size() <= 0) {
			ofLog(OF_LOG_NOTICE, "- please add vertex points -");
			return;
		}
		
		world			  = b2dworld;
		vertexCount		  = (int)vertices.size();
		poly.density	  = mass;
		poly.restitution  = bounce;
		poly.friction	  = friction;
		poly.vertexCount  = vertexCount;
		//printf("- num vertices: %i -\n", poly.vertexCount);
		
		if(vertexCount > b2_maxPolygonVertices) {
			vertexCount = b2_maxPolygonVertices;
			ofLog(OF_LOG_WARNING, "- to many vertices -");
		}
		
		
		
		
		/*
		 
		 
		 need to write something to test for bad polygons - ohh crap! 
		 
		 
		 */
		
		for(int i=0; i<vertexCount; i++) {
			poly.vertices[i].Set(vertices[i].x/OFX_BOX2D_SCALE, vertices[i].y/OFX_BOX2D_SCALE);
		}
		
		
		//Build Body for shape
		bodyDef.position.Set(x/OFX_BOX2D_SCALE, y/OFX_BOX2D_SCALE);
		body = world->CreateBody(&bodyDef);
		body->CreateShape(&poly);
		body->SetMassFromShapes();
		
		
		//printf("--- We built the shape \n---");
		
		// anything that you need called
		init();
	}
	
	//------------------------------------------------
	void draw() {
		if(body != NULL ) {
			
			ofEnableAlphaBlending();
			ofFill();
			ofSetColor(255, 0, 255, 100);
			ofBeginShape();
			for(int i=0; i<vertices.size(); i++) {
				ofVertex(vertices[i].x, vertices[i].y);
			}
			ofEndShape();
			ofDisableAlphaBlending();
			
			ofSetColor(0xffffff);
			ofPoint c = getCenter();
			ofCircle(c.x, c.y, 1);
			
			return;
			
			for(b2Shape* s=body->GetShapeList(); s; s=s->GetNext()) {
				
				const b2XForm&	xf		= body->GetXForm();		
				b2PolygonShape* poly	= (b2PolygonShape*)s;
				int				count	= poly->GetVertexCount();
				const b2Vec2*	verts	= poly->GetVertices();
				
				
				ofEnableAlphaBlending();
				ofFill();
				ofSetColor(255, 0, 255, 100);
				ofBeginShape();
				for(int j=0; j<count; j++) {
					b2Vec2 pt = b2Mul(xf, verts[j]);
					ofVertex(pt.x*OFX_BOX2D_SCALE, pt.y*OFX_BOX2D_SCALE);
				}
				ofEndShape();
				
				ofNoFill();
				ofSetColor(255, 255, 255);
				ofBeginShape();
				for(int j=0; j<count; j++) {
					b2Vec2 pt = b2Mul(xf, verts[j]);
					ofVertex(pt.x*OFX_BOX2D_SCALE, pt.y*OFX_BOX2D_SCALE);
				}
				ofEndShape(true);
				
				ofDisableAlphaBlending();
				
			}
			
		}
	}
};











