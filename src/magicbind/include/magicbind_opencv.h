#pragma once
// cv::Mat / cv::Point_ / cv::Point3_ / cv::Size_ / cv::Rect_ / cv::Scalar_
// <-> Python (numpy.ndarray / tuple) type casters for nanobind.
// OpenCV casters are compiled only when opencv2/core.hpp is reachable.
#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <type_traits>

#if __has_include(<opencv2/core.hpp>)
#include <opencv2/core.hpp>
#define MAGICBIND_HAS_OPENCV 1
#endif

#ifdef MAGICBIND_HAS_OPENCV

namespace nanobind {
namespace detail {

namespace mb_cv {

inline int fmt_to_depth(const char *fmt) noexcept {
    if (!fmt) return -1;
    switch (fmt[0]) {
        case 'B':           return CV_8U;
        case 'b':           return CV_8S;
        case 'H':           return CV_16U;
        case 'h':           return CV_16S;
        case 'i': case 'l': return CV_32S;
        case 'f':           return CV_32F;
        case 'd':           return CV_64F;
        default:            return -1;
    }
}

inline dlpack::dtype depth_to_dtype(int depth) noexcept {
    switch (depth) {
        case CV_8U:  return {1, 8,  1};
        case CV_8S:  return {0, 8,  1};
        case CV_16U: return {1, 16, 1};
        case CV_16S: return {0, 16, 1};
        case CV_32S: return {0, 32, 1};
        case CV_16F: return {2, 16, 1};
        case CV_32F: return {2, 32, 1};
        case CV_64F: return {2, 64, 1};
        default:     return {1, 8,  1};
    }
}

template <typename T>
inline PyObject* to_py(T v) noexcept {
    if constexpr (std::is_integral_v<T>)
        return PyLong_FromLongLong((long long)v);
    else
        return PyFloat_FromDouble((double)v);
}

template <typename T>
inline bool from_py(PyObject *o, T &out) noexcept {
    if constexpr (std::is_integral_v<T>) {
        long long v = PyLong_AsLongLong(o);
        if (v == -1 && PyErr_Occurred()) { PyErr_Clear(); return false; }
        out = (T)v;
    } else {
        double v = PyFloat_AsDouble(o);
        if (v == -1.0 && PyErr_Occurred()) { PyErr_Clear(); return false; }
        out = (T)v;
    }
    return true;
}

} // namespace mb_cv

// cv::Mat <-> numpy.ndarray
template <>
struct type_caster<cv::Mat> {
    NB_TYPE_CASTER(cv::Mat, const_name("numpy.ndarray"))

    bool from_python(handle src, uint8_t, cleanup_list *) noexcept {
        Py_buffer view;
        if (PyObject_GetBuffer(src.ptr(), &view,
                               PyBUF_FORMAT | PyBUF_C_CONTIGUOUS | PyBUF_ND) != 0) {
            PyErr_Clear();
            return false;
        }

        if (view.ndim < 2 || view.ndim > 3) {
            PyBuffer_Release(&view);
            return false;
        }

        int depth = mb_cv::fmt_to_depth(view.format);
        if (depth < 0) {
            PyBuffer_Release(&view);
            return false;
        }

        int channels = (view.ndim == 3) ? (int)view.shape[2] : 1;
        cv::Mat ref((int)view.shape[0], (int)view.shape[1],
                    CV_MAKETYPE(depth, channels), view.buf, (size_t)view.strides[0]);
        value = ref.clone();
        PyBuffer_Release(&view);
        return true;
    }

    static handle from_cpp(cv::Mat mat, rv_policy, cleanup_list *) noexcept {
        if (mat.empty())
            return none().release();

        cv::Mat *m = new cv::Mat(mat.clone());
        int channels = m->channels();
        int ndim     = (channels == 1) ? 2 : 3;

        size_t  shape[3]   = {(size_t)m->rows, (size_t)m->cols, (size_t)channels};
        int64_t strides[3] = {(int64_t)m->step[0],
                               (int64_t)m->step[1],
                               (int64_t)CV_ELEM_SIZE1(m->type())};

        capsule owner(m, [](void *p) noexcept { delete static_cast<cv::Mat *>(p); });

        return ndarray<numpy>(m->data, ndim, shape, owner,
                              strides, mb_cv::depth_to_dtype(m->depth())).cast().release();
    }
};

// cv::Point_<T> <-> (x, y)
template <typename T>
struct type_caster<cv::Point_<T>> {
    NB_TYPE_CASTER(cv::Point_<T>, const_name("tuple"))

    bool from_python(handle src, uint8_t, cleanup_list *) noexcept {
        PyObject *seq = PySequence_Fast(src.ptr(), "");
        if (!seq) { PyErr_Clear(); return false; }
        bool ok = false;
        if (PySequence_Fast_GET_SIZE(seq) == 2) {
            T x, y;
            if (mb_cv::from_py(PySequence_Fast_GET_ITEM(seq, 0), x) &&
                mb_cv::from_py(PySequence_Fast_GET_ITEM(seq, 1), y)) {
                value = {x, y};
                ok = true;
            }
        }
        Py_DECREF(seq);
        return ok;
    }

    static handle from_cpp(cv::Point_<T> p, rv_policy, cleanup_list *) noexcept {
        PyObject *t = PyTuple_New(2);
        if (!t) return {};
        PyTuple_SET_ITEM(t, 0, mb_cv::to_py(p.x));
        PyTuple_SET_ITEM(t, 1, mb_cv::to_py(p.y));
        return {t};
    }
};

// cv::Point3_<T> <-> (x, y, z)
template <typename T>
struct type_caster<cv::Point3_<T>> {
    NB_TYPE_CASTER(cv::Point3_<T>, const_name("tuple"))

    bool from_python(handle src, uint8_t, cleanup_list *) noexcept {
        PyObject *seq = PySequence_Fast(src.ptr(), "");
        if (!seq) { PyErr_Clear(); return false; }
        bool ok = false;
        if (PySequence_Fast_GET_SIZE(seq) == 3) {
            T x, y, z;
            if (mb_cv::from_py(PySequence_Fast_GET_ITEM(seq, 0), x) &&
                mb_cv::from_py(PySequence_Fast_GET_ITEM(seq, 1), y) &&
                mb_cv::from_py(PySequence_Fast_GET_ITEM(seq, 2), z)) {
                value = {x, y, z};
                ok = true;
            }
        }
        Py_DECREF(seq);
        return ok;
    }

    static handle from_cpp(cv::Point3_<T> p, rv_policy, cleanup_list *) noexcept {
        PyObject *t = PyTuple_New(3);
        if (!t) return {};
        PyTuple_SET_ITEM(t, 0, mb_cv::to_py(p.x));
        PyTuple_SET_ITEM(t, 1, mb_cv::to_py(p.y));
        PyTuple_SET_ITEM(t, 2, mb_cv::to_py(p.z));
        return {t};
    }
};

// cv::Size_<T> <-> (width, height)
template <typename T>
struct type_caster<cv::Size_<T>> {
    NB_TYPE_CASTER(cv::Size_<T>, const_name("tuple"))

    bool from_python(handle src, uint8_t, cleanup_list *) noexcept {
        PyObject *seq = PySequence_Fast(src.ptr(), "");
        if (!seq) { PyErr_Clear(); return false; }
        bool ok = false;
        if (PySequence_Fast_GET_SIZE(seq) == 2) {
            T w, h;
            if (mb_cv::from_py(PySequence_Fast_GET_ITEM(seq, 0), w) &&
                mb_cv::from_py(PySequence_Fast_GET_ITEM(seq, 1), h)) {
                value = {w, h};
                ok = true;
            }
        }
        Py_DECREF(seq);
        return ok;
    }

    static handle from_cpp(cv::Size_<T> s, rv_policy, cleanup_list *) noexcept {
        PyObject *t = PyTuple_New(2);
        if (!t) return {};
        PyTuple_SET_ITEM(t, 0, mb_cv::to_py(s.width));
        PyTuple_SET_ITEM(t, 1, mb_cv::to_py(s.height));
        return {t};
    }
};

// cv::Rect_<T> <-> (x, y, width, height)
template <typename T>
struct type_caster<cv::Rect_<T>> {
    NB_TYPE_CASTER(cv::Rect_<T>, const_name("tuple"))

    bool from_python(handle src, uint8_t, cleanup_list *) noexcept {
        PyObject *seq = PySequence_Fast(src.ptr(), "");
        if (!seq) { PyErr_Clear(); return false; }
        bool ok = false;
        if (PySequence_Fast_GET_SIZE(seq) == 4) {
            T x, y, w, h;
            if (mb_cv::from_py(PySequence_Fast_GET_ITEM(seq, 0), x) &&
                mb_cv::from_py(PySequence_Fast_GET_ITEM(seq, 1), y) &&
                mb_cv::from_py(PySequence_Fast_GET_ITEM(seq, 2), w) &&
                mb_cv::from_py(PySequence_Fast_GET_ITEM(seq, 3), h)) {
                value = {x, y, w, h};
                ok = true;
            }
        }
        Py_DECREF(seq);
        return ok;
    }

    static handle from_cpp(cv::Rect_<T> r, rv_policy, cleanup_list *) noexcept {
        PyObject *t = PyTuple_New(4);
        if (!t) return {};
        PyTuple_SET_ITEM(t, 0, mb_cv::to_py(r.x));
        PyTuple_SET_ITEM(t, 1, mb_cv::to_py(r.y));
        PyTuple_SET_ITEM(t, 2, mb_cv::to_py(r.width));
        PyTuple_SET_ITEM(t, 3, mb_cv::to_py(r.height));
        return {t};
    }
};

// cv::Scalar_<T> <-> tuple of 1-4 values
template <typename T>
struct type_caster<cv::Scalar_<T>> {
    NB_TYPE_CASTER(cv::Scalar_<T>, const_name("tuple"))

    bool from_python(handle src, uint8_t, cleanup_list *) noexcept {
        PyObject *seq = PySequence_Fast(src.ptr(), "");
        if (!seq) { PyErr_Clear(); return false; }
        Py_ssize_t sz = PySequence_Fast_GET_SIZE(seq);
        bool ok = (sz >= 1 && sz <= 4);
        if (ok) {
            value = {};
            for (Py_ssize_t i = 0; i < sz && ok; i++)
                ok = mb_cv::from_py(PySequence_Fast_GET_ITEM(seq, i), value[i]);
        }
        Py_DECREF(seq);
        return ok;
    }

    static handle from_cpp(cv::Scalar_<T> s, rv_policy, cleanup_list *) noexcept {
        PyObject *t = PyTuple_New(4);
        if (!t) return {};
        for (int i = 0; i < 4; i++)
            PyTuple_SET_ITEM(t, i, mb_cv::to_py(s[i]));
        return {t};
    }
};

}} // namespace nanobind::detail

#endif // MAGICBIND_HAS_OPENCV
