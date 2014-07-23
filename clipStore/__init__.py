'''
The clipStore.clip_source.ClipSource is a class representing a clip, which can be a movie or an image sequence.
It stores attributes like source path, source range, play range, source audio.

It can be decorated with production data via function set_publish_entity.  Hence the object can represent
a published clip or a local clip. 

Clip source also provides ability to resolve the source's range if not specified.  
For movie, it determines the source range using ffmpeg.    

Example Code:

##### create a mono movie clip source #####

MEDIA_SAMPLE_ROOT = "/systeme/softs/unit_test_data/"

movie_clip = ClipSource( MEDIA_SAMPLE_ROOT + "movie/movie_small.mov" )

# clip source automatically determine the range.
assert movie_clip.source_range() == (101, 177)        
assert movie_clip.source_path()  == MEDIA_SAMPLE_ROOT + "movie/movie_small.mov"         


##### create a stereo frame clip source #####

frames_clip = ClipSource( MEDIA_SAMPLE_ROOT + "img_seq/fake_sequence/dummy_frame.l.0101.jpg" )
 
# clip source automatically determine the range.
assert frames_clip.source_range()==(101, 109)

assert frames_clip.source_path(flg_stereo=True) == [ MEDIA_SAMPLE_ROOT + "img_seq/fake_sequence/dummy_frame.l.####.jpg", 
                                                    MEDIA_SAMPLE_ROOT + "img_seq/fake_sequence/dummy_frame.r.####.jpg"
                                                  ]
                                          

##### get the play data #####
# By default the play range is the same is the source range, but you can specify any range.
# If the play range is out of bounds, clip source will inform the head frame hold and tail frame hold.

mono_clip = ClipSource( MEDIA_SAMPLE_ROOT + "img_seq/fake_mono_sequence/dummy_frame.l.####.jpg" )
assert mono_clip.source_range()==(101, 109)
assert mono_clip.get_play_data() == (None, 101, 109, None) 

# play out of range for head portion
cs = ClipSource( MEDIA_SAMPLE_ROOT + "img_seq/fake_mono_sequence/dummy_frame.l.####.jpg",                                     
                            play_in = 80, play_out = 106 )

# play data show that you need to hold frame 101 for 21 frames
assert cs.get_play_data()==(21, 101, 106, None)

assert cs.play_range()==(80, 106)
  
'''