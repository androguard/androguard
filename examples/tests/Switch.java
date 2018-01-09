class Switch {

    public int someSwitch(int x, String y) {
        int r = 0;
        switch (x) {
            case 1:
                r = 23;
                break;
            case 2:
                r = 42;
                break;
            case 3:
                r = 72;
                break;
            default:
                r = 17;
                break;
        }
        if (y != null) {
            r = 99;
        }
        return r;
    }
}
