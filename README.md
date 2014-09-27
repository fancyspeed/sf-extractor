This project contains 2 Html Conent Extractors:

1. <b>cx-extractor</b> in python. Reference:  https://github.com/amumu/cx-extractor

2. <b>sf-extractor</b>, a new extractor according to dynamic block segmentation and statistics. Steps:

  2.1. remove newline characters
  
  2.2. remove tags, replace with newlines
  
  2.3. get blocks
  
  2.4. stat each block's text/stopword/link/punctuation densities
  
  2.5. get the best block
  
  2.6. merge it's neighbours
