def test(a):
    if a is None:
        print 'is none'
    if a is not None:
        print 'is not none'
    if a:
        print 'is true'
    if not a:
        print 'is not true'
    print ''

if __name__ == '__main__':
    test(None)
    test(1)
    test(0)
    test('')
    test('a')
