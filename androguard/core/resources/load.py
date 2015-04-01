
def init():
  from public import resources

  return  {
          "attributes": {
              "forward": {k: v for k, v in resources['attr'].iteritems()},
              "inverse": {v: k for k, v in resources['attr'].iteritems()}
          },
          "styles": {
              "forward": {k: v for k, v in resources['style'].iteritems()},
              "inverse": {v: k for k, v in resources['style'].iteritems()}
          }
  }

