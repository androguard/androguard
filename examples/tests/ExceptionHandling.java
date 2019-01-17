public class ExceptionHandling {

    public void someMethod() throws SomeException {
        throw new SomeException("This is an exception!");
    }

    public int mightThrowSomething(int i) throws AnotherException {
        if ( i == 42 ) {
            throw new AnotherException("42 was not found");
        }
        else {
            return i * 2;
        } 
    }

    public void differentExceptions(int i) throws SomeException, AnotherException {
        if ( i == 42 ) {
            throw new SomeException("42 is the answer");
        }
        else {
            throw new AnotherException("must provide the answer");
        }
    }


}

class SomeException extends Exception {
    public SomeException(String msg) {
    }

}

class AnotherException extends Exception {
    public AnotherException(String msg) {
    }

}
