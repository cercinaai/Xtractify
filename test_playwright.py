from src.utils.b2_util import upload_image_to_b2

test_url = "https://img.leboncoin.fr/api/v1/lbcpb1/images/b4/f8/3b/b4f83b9b27dc12269be78db151f6de4cbb6d0407.jpg?rule=ad-image"
print(upload_image_to_b2(test_url))