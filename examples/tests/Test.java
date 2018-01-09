class Test{

    public int aTestMethod(int z){
        int x = 23;

        x = (x - z) | 72 - (2 * x) & 0x42 + z;

        return x;
    }
}
