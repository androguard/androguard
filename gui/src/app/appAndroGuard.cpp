#include "appAndroGuard.h"

AndroGuardObject::AndroGuardObject()
{



}
AndroGuardObject::~AndroGuardObject()
{



}

appAndroGuard::appAndroGuard()
{
    Py_Initialize();
    PyEval_InitThreads();

    PyRun_SimpleString("from time import time,ctime\n"
                     "print 'Today is',ctime(time())\n");
}

appAndroGuard::~appAndroGuard()
{
    Py_Finalize();
}
