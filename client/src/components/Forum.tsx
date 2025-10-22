


import React, { useState, useEffect } from "react";
import { FaPlus } from "react-icons/fa";
import "./Forum.css";
import { toast } from "react-toastify";

interface Comment {
  id: number;
  post_id: number;
  doctor_id: number;
  content: string;
}

interface Report {
  id: number;
  title: string;
  description: string;
}

interface Post {
  id: number;
  doctor_id: number;
  title: string;
  content: string;
  category: string;
  likes: number;
  comments: Comment[];
  report: Report | null; // Allow report to be nullable
}

const Forum: React.FC = () => {
  const [posts, setPosts] = useState<Post[]>([]);
  const [newPost, setNewPost] = useState<Post>({
    id: 0,
    doctor_id: 0,
    title: "",
    content: "",
    category: "General",
    likes: 0,
    comments: [],
    report: null,
  });

  const [showPostForm, setShowPostForm] = useState(false);
  const [visibleComments, setVisibleComments] = useState<{ [key: number]: boolean }>({});

  useEffect(() => {
    const fetchPosts = async () => {
      try {
        const response = await fetch("http://127.0.0.1:5000/posts");
        if (response.ok) {
          const data: Post[] = await response.json();
          setPosts(data);
        } else {
          toast.error("Failed to fetch posts.");
        }
      } catch (error) {
        console.error("Error fetching posts:", error);
        toast.error("Error fetching posts.");
      }
    };

    fetchPosts();
  }, []);

  const handleNewPostChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setNewPost((prev) => ({ ...prev, [name]: value }));
  };

  const handleAddPost = async () => {
    const doctorId = sessionStorage.getItem("doctorId");
    if (!doctorId) {
      toast.error("You are not logged in.");
      return;
    }

    if (newPost.title && newPost.content) {
      try {
        const response = await fetch("http://127.0.0.1:5000/posts", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ...newPost, doctor_id: parseInt(doctorId) }),
        });

        if (response.ok) {
          const newPostData = await response.json();
          setPosts([
            ...posts,
            { ...newPost, id: newPostData.id, doctor_id: parseInt(doctorId), likes: 0, comments: [] },
          ]);
          setNewPost({ ...newPost, title: "", content: "", category: "General", report: null });
          setShowPostForm(false);
        } else {
          toast.error("Failed to create post.");
        }
      } catch (error) {
        console.error("Error creating post:", error);
      }
    } else {
      toast.error("Title and content are required.");
    }
  };

  const handleAddComment = async (postId: number, content: string) => {
    const doctorId = sessionStorage.getItem("doctorId");
    if (!doctorId) {
      toast.error("You are not logged in.");
      return;
    }

    if (content) {
      try {
        const response = await fetch(`http://127.0.0.1:5000/posts/${postId}/comments`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ doctor_id: parseInt(doctorId), content }),
        });

        if (response.ok) {
          const commentId = (await response.json()).id;
          setPosts((prevPosts) =>
            prevPosts.map((post) =>
              post.id === postId
                ? {
                    ...post,
                    comments: [
                      ...post.comments,
                      { id: commentId, post_id: postId, doctor_id: parseInt(doctorId), content },
                    ],
                  }
                : post
            )
          );
        } else {
          toast.error("Failed to add comment.");
        }
      } catch (error) {
        console.error("Error adding comment:", error);
      }
    }
  };

  const toggleCommentsVisibility = (postId: number) => {
    setVisibleComments((prev) => ({ ...prev, [postId]: !prev[postId] }));
  };

  return (
    <div className="forum-wrapper">
      <div className="forum-header">Collaborative Forum</div>

      <button className="new-post-btn" onClick={() => setShowPostForm(true)}>
        <FaPlus />
      </button>

      {showPostForm && (
        <div className="new-post-modal">
          <div className="new-post-container">
            <h3>Create a New Post</h3>
            <input
              type="text"
              name="title"
              placeholder="Post Title"
              value={newPost.title}
              onChange={handleNewPostChange}
            />
            <textarea
              name="content"
              placeholder="Write your case or question here..."
              value={newPost.content}
              onChange={handleNewPostChange}
            />
            <select name="category" value={newPost.category} onChange={handleNewPostChange}>
              <option value="General">General</option>
              <option value="Radiology">Radiology</option>
              <option value="Cardiology">Cardiology</option>
              <option value="Pathology">Pathology</option>
            </select>
            <div className="modal-buttons">
              <button onClick={() => setShowPostForm(false)}>Cancel</button>
              <button onClick={handleAddPost}>Post</button>
            </div>
          </div>
        </div>
      )}

      <div className="posts-container">
        {posts.map((post) => (
          <div className="post-item" key={post.id}>
            <h3>{post.title}</h3>
            <p>{post.content}</p>
            <p>
              <strong>Category:</strong> {post.category}
            </p>
            <div className="comments-section">
              <h4>Comments:</h4>
              {post.comments
                .slice(0, visibleComments[post.id] ? post.comments.length : 1)
                .map((comment) => (
                  <div className="comment-box" key={comment.id}>
                    <p>{comment.content}</p>
                  </div>
                ))}
              {post.comments.length > 1 && (
                <button
                  className="view-comments-btn"
                  onClick={() => toggleCommentsVisibility(post.id)}
                >
                  {visibleComments[post.id] ? "Hide Comments" : "View All Comments"}
                </button>
              )}

              <input
                type="text"
                placeholder="Add a comment..."
                onKeyDown={(e) => {
                  if (e.key === "Enter" && e.currentTarget.value) {
                    handleAddComment(post.id, e.currentTarget.value);
                    e.currentTarget.value = "";
                  }
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Forum;
