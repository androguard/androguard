/*
* Copyright (c) 2006-2007 Erin Catto http://www.gphysics.com
*
* This software is provided 'as-is', without any express or implied
* warranty.  In no event will the authors be held liable for any damages
* arising from the use of this software.
* Permission is granted to anyone to use this software for any purpose,
* including commercial applications, and to alter it and redistribute it
* freely, subject to the following restrictions:
* 1. The origin of this software must not be misrepresented; you must not
* claim that you wrote the original software. If you use this software
* in a product, an acknowledgment in the product documentation would be
* appreciated but is not required.
* 2. Altered source versions must be plainly marked as such, and must not be
* misrepresented as being the original software.
* 3. This notice may not be removed or altered from any source distribution.
*/

#include "b2PolyAndEdgeContact.h"
#include "../b2Body.h"
#include "../b2WorldCallbacks.h"
#include "../../Common/b2BlockAllocator.h"
#include "../../Collision/Shapes/b2EdgeShape.h"
#include "../../Collision/Shapes/b2PolygonShape.h"

#include <new>
#include <cstring>

b2Contact* b2PolyAndEdgeContact::Create(b2Shape* shape1, b2Shape* shape2, b2BlockAllocator* allocator)
{
	void* mem = allocator->Allocate(sizeof(b2PolyAndEdgeContact));
	return new (mem) b2PolyAndEdgeContact(shape1, shape2);
}

void b2PolyAndEdgeContact::Destroy(b2Contact* contact, b2BlockAllocator* allocator)
{
	((b2PolyAndEdgeContact*)contact)->~b2PolyAndEdgeContact();
	allocator->Free(contact, sizeof(b2PolyAndEdgeContact));
}

b2PolyAndEdgeContact::b2PolyAndEdgeContact(b2Shape* s1, b2Shape* s2)
: b2Contact(s1, s2)
{
	b2Assert(m_shape1->GetType() == e_polygonShape);
	b2Assert(m_shape2->GetType() == e_edgeShape);
	m_manifold.pointCount = 0;
}

void b2PolyAndEdgeContact::Evaluate(b2ContactListener* listener)
{
	b2Body* b1 = m_shape1->GetBody();
	b2Body* b2 = m_shape2->GetBody();

	b2Manifold m0;
	memcpy(&m0, &m_manifold, sizeof(b2Manifold));

	b2CollidePolyAndEdge(&m_manifold, (b2PolygonShape*)m_shape1, b1->GetXForm(), (b2EdgeShape*)m_shape2, b2->GetXForm());

	bool persisted[b2_maxManifoldPoints] = {false, false};

	b2ContactPoint cp;
	cp.shape1 = m_shape1;
	cp.shape2 = m_shape2;
	cp.friction = b2MixFriction(m_shape1->GetFriction(), m_shape2->GetFriction());
	cp.restitution = b2MixRestitution(m_shape1->GetRestitution(), m_shape2->GetRestitution());

	// Match contact ids to facilitate warm starting.
	if (m_manifold.pointCount > 0)
	{
		// Match old contact ids to new contact ids and copy the
		// stored impulses to warm start the solver.
		for (int32 i = 0; i < m_manifold.pointCount; ++i)
		{
			b2ManifoldPoint* mp = m_manifold.points + i;
			mp->normalImpulse = 0.0f;
			mp->tangentImpulse = 0.0f;
			bool found = false;
			b2ContactID id = mp->id;

			for (int32 j = 0; j < m0.pointCount; ++j)
			{
				if (persisted[j] == true)
				{
					continue;
				}

				b2ManifoldPoint* mp0 = m0.points + j;

				if (mp0->id.key == id.key)
				{
					persisted[j] = true;
					mp->normalImpulse = mp0->normalImpulse;
					mp->tangentImpulse = mp0->tangentImpulse;

					// A persistent point.
					found = true;

					// Report persistent point.
					if (listener != NULL)
					{
						cp.position = b1->GetWorldPoint(mp->localPoint1);
						b2Vec2 v1 = b1->GetLinearVelocityFromLocalPoint(mp->localPoint1);
						b2Vec2 v2 = b2->GetLinearVelocityFromLocalPoint(mp->localPoint2);
						cp.velocity = v2 - v1;
						cp.normal = m_manifold.normal;
						cp.separation = mp->separation;
						cp.id = id;
						listener->Persist(&cp);
					}
					break;
				}
			}

			// Report added point.
			if (found == false && listener != NULL)
			{
				cp.position = b1->GetWorldPoint(mp->localPoint1);
				b2Vec2 v1 = b1->GetLinearVelocityFromLocalPoint(mp->localPoint1);
				b2Vec2 v2 = b2->GetLinearVelocityFromLocalPoint(mp->localPoint2);
				cp.velocity = v2 - v1;
				cp.normal = m_manifold.normal;
				cp.separation = mp->separation;
				cp.id = id;
				listener->Add(&cp);
			}
		}

		m_manifoldCount = 1;
	}
	else
	{
		m_manifoldCount = 0;
	}

	if (listener == NULL)
	{
		return;
	}

	// Report removed points.
	for (int32 i = 0; i < m0.pointCount; ++i)
	{
		if (persisted[i])
		{
			continue;
		}

		b2ManifoldPoint* mp0 = m0.points + i;
		cp.position = b1->GetWorldPoint(mp0->localPoint1);
		b2Vec2 v1 = b1->GetLinearVelocityFromLocalPoint(mp0->localPoint1);
		b2Vec2 v2 = b2->GetLinearVelocityFromLocalPoint(mp0->localPoint2);
		cp.velocity = v2 - v1;
		cp.normal = m0.normal;
		cp.separation = mp0->separation;
		cp.id = mp0->id;
		listener->Remove(&cp);
	}
}

void b2PolyAndEdgeContact::b2CollidePolyAndEdge(b2Manifold* manifold,
														  const b2PolygonShape* polygon, 
														  const b2XForm& xf1,
														  const b2EdgeShape* edge, 
														  const b2XForm& xf2)
{
	manifold->pointCount = 0;
	b2Vec2 v1 = b2Mul(xf2, edge->GetVertex1());
	b2Vec2 v2 = b2Mul(xf2, edge->GetVertex2());
	b2Vec2 n = b2Mul(xf2.R, edge->GetNormalVector());
	b2Vec2 v1Local = b2MulT(xf1, v1);
	b2Vec2 v2Local = b2MulT(xf1, v2);
	b2Vec2 nLocal = b2MulT(xf1.R, n);
		
	float32 separation1;
	int32 separationIndex1 = -1; // which normal on the poly found the shallowest depth?
	float32 separationMax1 = -B2_FLT_MAX; // the shallowest depth of edge in poly
	float32 separation2;
	int32 separationIndex2 = -1; // which normal on the poly found the shallowest depth?
	float32 separationMax2 = -B2_FLT_MAX; // the shallowest depth of edge in poly
	float32 separationMax = -B2_FLT_MAX; // the shallowest depth of edge in poly
	bool separationV1 = false; // is the shallowest depth from edge's v1 or v2 vertex?
	int32 separationIndex = -1; // which normal on the poly found the shallowest depth?
		
	int32 vertexCount = polygon->GetVertexCount();
	const b2Vec2* vertices = polygon->GetVertices();
	const b2Vec2* normals = polygon->GetNormals();
		
	int32 enterStartIndex = -1; // the last poly vertex above the edge
	int32 enterEndIndex = -1; // the first poly vertex below the edge
	int32 exitStartIndex = -1; // the last poly vertex below the edge
	int32 exitEndIndex = -1; // the first poly vertex above the edge
	//int32 deepestIndex;
	
	// the "N" in the following variables refers to the edge's normal. 
	// these are projections of poly vertices along the edge's normal, 
	// a.k.a. they are the separation of the poly from the edge. 
	float32 prevSepN = 0.0f;
	float32 nextSepN = 0.0f;
	float32 enterSepN = 0.0f; // the depth of enterEndIndex under the edge (stored as a separation, so it's negative)
	float32 exitSepN = 0.0f; // the depth of exitStartIndex under the edge (stored as a separation, so it's negative)
	float32 deepestSepN = B2_FLT_MAX; // the depth of the deepest poly vertex under the end (stored as a separation, so it's negative)
	
	
	// for each poly normal, get the edge's depth into the poly. 
	// for each poly vertex, get the vertex's depth into the edge. 
	// use these calculations to define the remaining variables declared above.
	prevSepN = b2Dot(vertices[vertexCount-1] - v1Local, nLocal);
	for (int32 i = 0; i < vertexCount; i++)
	{
		separation1 = b2Dot(v1Local - vertices[i], normals[i]);
		separation2 = b2Dot(v2Local - vertices[i], normals[i]);
		if (separation2 < separation1) {
			if (separation2 > separationMax) {
				separationMax = separation2;
				separationV1 = false;
				separationIndex = i;
			}
		} else {
			if (separation1 > separationMax) {
				separationMax = separation1;
				separationV1 = true;
				separationIndex = i;
			}
		}
		if (separation1 > separationMax1) {
			separationMax1 = separation1;
			separationIndex1 = i;
		}
		if (separation2 > separationMax2) {
			separationMax2 = separation2;
			separationIndex2 = i;
		}
		
		nextSepN = b2Dot(vertices[i] - v1Local, nLocal);
		if (nextSepN >= 0.0f && prevSepN < 0.0f) {
			exitStartIndex = (i == 0) ? vertexCount-1 : i-1;
			exitEndIndex = i;
			exitSepN = prevSepN;
		} else if (nextSepN < 0.0f && prevSepN >= 0.0f) {
			enterStartIndex = (i == 0) ? vertexCount-1 : i-1;
			enterEndIndex = i;
			enterSepN = nextSepN;
		}
		if (nextSepN < deepestSepN) {
			deepestSepN = nextSepN;
			//deepestIndex = i;
		}
		prevSepN = nextSepN;
	}
	
	if (enterStartIndex == -1) {
		// poly is entirely below or entirely above edge, return with no contact:
		return;
	}
	if (separationMax > 0.0f) {
		// poly is laterally disjoint with edge, return with no contact:
		return;
	}
	
	// if the poly is near a convex corner on the edge
	if ((separationV1 && edge->Corner1IsConvex()) || (!separationV1 && edge->Corner2IsConvex())) {
		// if shallowest depth was from edge into poly, 
		// use the edge's vertex as the contact point:
		if (separationMax > deepestSepN + b2_linearSlop) {
			// if -normal angle is closer to adjacent edge than this edge, 
			// let the adjacent edge handle it and return with no contact:
			if (separationV1) {
				if (b2Dot(normals[separationIndex1], b2MulT(xf1.R, b2Mul(xf2.R, edge->GetCorner1Vector()))) >= 0.0f) {
					return;
				}
			} else {
				if (b2Dot(normals[separationIndex2], b2MulT(xf1.R, b2Mul(xf2.R, edge->GetCorner2Vector()))) <= 0.0f) {
					return;
				}
			}
			
			manifold->pointCount = 1;
			manifold->normal = b2Mul(xf1.R, normals[separationIndex]);
			manifold->points[0].separation = separationMax;
			manifold->points[0].id.features.incidentEdge = (uint8)separationIndex;
			manifold->points[0].id.features.incidentVertex = b2_nullFeature;
			manifold->points[0].id.features.referenceEdge = 0;
			manifold->points[0].id.features.flip = 0;
			if (separationV1) {
				manifold->points[0].localPoint1 = v1Local;
				manifold->points[0].localPoint2 = edge->GetVertex1();
			} else {
				manifold->points[0].localPoint1 = v2Local;
				manifold->points[0].localPoint2 = edge->GetVertex2();
			}
			return;
		}
	}
	
	// We're going to use the edge's normal now.
	manifold->normal = (-1.0f) * n;
	
	// Check whether we only need one contact point.
	if (enterEndIndex == exitStartIndex) {
		manifold->pointCount = 1;
		manifold->points[0].id.features.incidentEdge = (uint8)enterEndIndex;
		manifold->points[0].id.features.incidentVertex = b2_nullFeature;
		manifold->points[0].id.features.referenceEdge = 0;
		manifold->points[0].id.features.flip = 0;
		manifold->points[0].localPoint1 = vertices[enterEndIndex];
		manifold->points[0].localPoint2 = b2MulT(xf2, b2Mul(xf1, vertices[enterEndIndex]));
		manifold->points[0].separation = enterSepN;
		return;
	}
		
	manifold->pointCount = 2;
	
	// dirLocal should be the edge's direction vector, but in the frame of the polygon.
	b2Vec2 dirLocal = b2Cross(nLocal, -1.0f); // TODO: figure out why this optimization didn't work
	//b2Vec2 dirLocal = b2MulT(xf1.R, b2Mul(xf2.R, edge->GetDirectionVector()));
	
	float32 dirProj1 = b2Dot(dirLocal, vertices[enterEndIndex] - v1Local);
	float32 dirProj2;
	
	// The contact resolution is more robust if the two manifold points are 
	// adjacent to each other on the polygon. So pick the first two poly
	// vertices that are under the edge:
	exitEndIndex = (enterEndIndex == vertexCount - 1) ? 0 : enterEndIndex + 1;
	if (exitEndIndex != exitStartIndex) {
		exitStartIndex = exitEndIndex;
		exitSepN = b2Dot(nLocal, vertices[exitStartIndex] - v1Local);
	}
	dirProj2 = b2Dot(dirLocal, vertices[exitStartIndex] - v1Local);
	
	manifold->points[0].id.features.incidentEdge = (uint8)enterEndIndex;
	manifold->points[0].id.features.incidentVertex = b2_nullFeature;
	manifold->points[0].id.features.referenceEdge = 0;
	manifold->points[0].id.features.flip = 0;
	
	if (dirProj1 > edge->GetLength()) {
		manifold->points[0].localPoint1 = v2Local;
		manifold->points[0].localPoint2 = edge->GetVertex2();
		float32 ratio = (edge->GetLength() - dirProj2) / (dirProj1 - dirProj2);
		if (ratio > 100.0f * B2_FLT_EPSILON && ratio < 1.0f) {
			manifold->points[0].separation = exitSepN * (1.0f - ratio) + enterSepN * ratio;
		} else {
			manifold->points[0].separation = enterSepN;
		}
	} else {
		manifold->points[0].localPoint1 = vertices[enterEndIndex];
		manifold->points[0].localPoint2 = b2MulT(xf2, b2Mul(xf1, vertices[enterEndIndex]));
		manifold->points[0].separation = enterSepN;
	}
		
	manifold->points[1].id.features.incidentEdge = (uint8)exitStartIndex;
	manifold->points[1].id.features.incidentVertex = b2_nullFeature;
	manifold->points[1].id.features.referenceEdge = 0;
	manifold->points[1].id.features.flip = 0;
		
	if (dirProj2 < 0.0f) {
		manifold->points[1].localPoint1 = v1Local;
		manifold->points[1].localPoint2 = edge->GetVertex1();
		float32 ratio = (-dirProj1) / (dirProj2 - dirProj1);
		if (ratio > 100.0f * B2_FLT_EPSILON && ratio < 1.0f) {
			manifold->points[1].separation = enterSepN * (1.0f - ratio) + exitSepN * ratio;
		} else {
			manifold->points[1].separation = exitSepN;
		}
	} else {
		manifold->points[1].localPoint1 = vertices[exitStartIndex];
		manifold->points[1].localPoint2 = b2MulT(xf2, b2Mul(xf1, vertices[exitStartIndex]));
		manifold->points[1].separation = exitSepN;
	}
}
