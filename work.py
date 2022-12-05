import bpy
import time
import queue
from .interfaces import SCG_Cycler_Context_Interface as Context_Interface

# This is called to make the WorkQueue do its thing
def work_tick():
    start_time = time.time()
    current_time = start_time
    cutoff_time = start_time + 0.1  # So we can process multiple jobs in an update, and not hang from the queue constantly filling
    if bpy.context.scene.scg_cycler_context.action and WorkQueue().job_queue.empty():
        WorkQueue().add(AutoUpdateJob())
    while current_time < cutoff_time and not WorkQueue().job_queue.empty(): # Only work when we have time and shit to do
        WorkQueue().process()
        current_time = time.time()
    return 0.5

class WorkQueue(Context_Interface):
    # Singleton job queue
    job_queue = queue.Queue()

    def add(self, job):
        self.job_queue.put(job)

    def process(self):
        if not self.job_queue.empty(): # Not really needed, but doesn't hurt to be safe for now
            next_job = self.job_queue.get()
            next_job.work()
            self.job_queue.task_done()

class Job(Context_Interface):
    def __init__(self, type):
        self.type = type
        self.work_queue = WorkQueue() # Easy accessor to the queue for jobs, so that they can add their own jobs, but not really needed since the queue is a singleton

    def work(self):
        return

# Inserts a keyframe into the target fcurve
class AddKeyframeJob(Job):
    def __init__(self, fcurve, frame, value, amplitude=None, back=None, easing=None, left_handle_type=None, right_handle_type=None, left_handle=None, right_handle=None, interpolation=None, period=None, type=None):
        Job.__init__(self, "ADD_KEYFRAME")
        self.fcurve = fcurve
        self.frame = frame
        self.value = value
        self.amplitude = amplitude
        self.back = back
        self.easing = easing
        self.left_handle_type = left_handle_type
        self.right_handle_type = right_handle_type
        self.left_handle = left_handle
        self.right_handle = right_handle
        self.interpolation = interpolation
        self.period = period
        self.type = type

    def work(self):
        keyframe = self.fcurve.keyframe_points.insert(self.frame, self.value)
        if self.amplitude is not None:
            keyframe.amplitude = self.amplitude
        if self.back is not None:
            keyframe.back = self.back
        if self.easing is not None:
            keyframe.easing = self.easing
        if self.left_handle_type is not None:
            keyframe.handle_left_type = self.left_handle_type
        if self.right_handle_type is not None:
            keyframe.handle_right_type = self.right_handle_type
        if self.left_handle is not None:
            keyframe.handle_left[0] = self.left_handle[0]
            keyframe.handle_left[1] = self.left_handle[1]
        if self.right_handle is not None:
            keyframe.handle_right[0] = self.right_handle[0]
            keyframe.handle_right[1] = self.right_handle[1]
        if self.interpolation is not None:
            keyframe.interpolation = self.interpolation
        if self.period is not None:
            keyframe.period = self.period
        if self.type is not None:
            keyframe.type = self.type

# Removes a specific keyframe from the target fcurve
class RemoveKeyframeJob(Job):
    def __init__(self, fcurve, frame):
        Job.__init__(self, "REMOVE_KEYFRAME")
        self.fcurve = fcurve
        self.frame = frame

    def work(self):
        for keyframe_point in self.fcurve.keyframe_points:
            if keyframe_point.co[0] == self.frame:
                self.fcurve.keyframe_points.remove(keyframe_point)
                return

# Changes the frame of a keyframe
class MoveKeyframeJob(Job):
    def __init__(self, keyframe, new_frame):
        Job.__init__(self, "MOVE_KEYFRAME")
        self.keyframe = keyframe
        self.new_frame = new_frame

    def work(self):
        old_pos = self.keyframe.co[0]
        difference = self.new_frame - old_pos
        self.keyframe.co[0] = self.new_frame
        self.keyframe.handle_left[0] + difference
        self.keyframe.handle_right[0] + difference

# Changes the value of a keyframe
class ChangeKeyframeValueJob(Job):
    def __init__(self, keyframe, new_value, amplitude=None, back=None, easing=None, left_handle_type=None, right_handle_type=None, left_handle=None, right_handle=None, interpolation=None, period=None, type=None):
        Job.__init__(self, "CHANGE_KEYFRAME_VALUE")
        self.keyframe = keyframe
        self.new_value = new_value
        self.amplitude = amplitude
        self.back = back
        self.easing = easing
        self.left_handle_type = left_handle_type
        self.right_handle_type = right_handle_type
        self.left_handle = left_handle
        self.right_handle = right_handle
        self.interpolation = interpolation
        self.period = period
        self.type = type

    def work(self):
        self.keyframe.co[1] = self.new_value
        if self.amplitude is not None:
            self.keyframe.amplitude = self.amplitude
        if self.back is not None:
            self.keyframe.back = self.back
        if self.easing is not None:
            self.keyframe.easing = self.easing
        if self.left_handle_type is not None:
            self.keyframe.handle_left_type = self.left_handle_type
        if self.right_handle_type is not None:
            self.keyframe.handle_right_type = self.right_handle_type
        if self.left_handle is not None:
            self.keyframe.handle_left[0] = self.left_handle[0]
            self.keyframe.handle_left[1] = self.left_handle[1]
        if self.right_handle is not None:
            self.keyframe.handle_right[0] = self.right_handle[0]
            self.keyframe.handle_right[1] = self.right_handle[1]
        if self.interpolation is not None:
            self.keyframe.interpolation = self.interpolation
        if self.period is not None:
            self.keyframe.period = self.period
        if self.type is not None:
            self.keyframe.type = self.type

class UpdateFCurveJob(Job):
    def __init__(self, fcurve):
        Job.__init__(self, "UPDATE_FCURVE")
        self.fcurve = fcurve

    def work(self):
        self.fcurve.update()         

class ResizeAnimationJob(Job):
    def __init__(self, old_animation_length, new_animation_length, old_fps, new_fps):
        Job.__init__(self, "RESIZE_ANIMATION")
        self.old_animation_length = old_animation_length
        self.new_animation_length = new_animation_length
        self.old_fps = old_fps
        self.new_fps = new_fps

    def work(self):      
        num_animated_frames = round(self.new_animation_length * self.new_fps)
        half_point = num_animated_frames / 2

        frame = 0.0
        for marker in self.cycler.timings.frame_markers:        
            marker.frame = frame
            frame += (marker.length/100.0) * num_animated_frames

        bpy.context.scene.timeline_markers.clear()
        for index, marker in enumerate(self.cycler.timings.frame_markers):
            marker_1 = bpy.context.scene.timeline_markers.new("{0} 1".format(marker.name), frame=marker.frame)
            marker_2 = bpy.context.scene.timeline_markers.new("{0} 2".format(marker.name), frame=marker.frame+half_point)
            if index == 0:
                marker_3 = bpy.context.scene.timeline_markers.new("{0} 1".format(marker.name), frame=num_animated_frames)

        bpy.context.scene.render.fps = self.new_fps
        bpy.context.scene.frame_start = 0
        bpy.context.scene.frame_end = num_animated_frames

        for control in self.cycler.controls:
            for channel in control:
                if channel.fcurve is None or (channel.control.mirrored and channel.mirror_fcurve is None):
                    continue

                old_num_frames = round(self.old_animation_length * self.old_fps)
                old_half_point = old_num_frames / 2

                new_num_frames = round(self.new_animation_length * self.new_fps)
                new_half_point = new_num_frames / 2

                frames = {}

                for index, keyframe in enumerate(channel):
                    old_first = round(keyframe.frame_marker.old_frame + ((keyframe.offset/100)*old_num_frames))
                    new_first = round(keyframe.frame_marker.frame + ((keyframe.offset/100)*new_num_frames))
                    frames[old_first] = new_first

                    if not channel.control.mirrored:
                        old_mirror = old_first + old_half_point
                        new_mirror = new_first + new_half_point
                        frames[old_mirror] = new_mirror
                    if index == 0:
                        old_end = old_first + old_num_frames
                        new_end = new_first + new_num_frames
                        frames[old_end] = new_end

                if channel.control.mirrored:
                    for keyframe in channel.mirror_channel:
                        old_mirror = round(keyframe.frame_marker.old_frame + ((keyframe.offset/100)*old_num_frames) + old_half_point)
                        new_mirror = round(keyframe.frame_marker.frame + ((keyframe.offset/100)*new_num_frames) + new_half_point)
                        frames[old_mirror] = new_mirror            

                for keyframe_point in channel.fcurve.keyframe_points:
                    if keyframe_point.co[0] in frames:
                        self.work_queue.add(MoveKeyframeJob(keyframe_point, frames[keyframe_point.co[0]]))
                    else:
                        self.work_queue.add(RemoveKeyframeJob(channel.fcurve, keyframe_point.co[0]))

                self.work_queue.add(UpdateFCurveJob(channel.fcurve))  

class UpdateKeyframeOffsetJob(Job):
    def __init__(self, keyframe, old_offset, new_offset):
        Job.__init__(self, "UPDATE_OFFSET")
        self.keyframe = keyframe
        self.old_offset = old_offset
        self.new_offset = new_offset

    def work(self):
        for control in self.cycler.controls:
            for channel in control:
                for keyframe in channel:
                    if self.keyframe == keyframe:

                        if channel.fcurve is None or (channel.control.mirrored and channel.mirror_fcurve is None):
                            return
                        
                        keyframe_points = {keyframe_point.co[0]:keyframe_point for keyframe_point in channel.fcurve.keyframe_points}                        
                        num_frames = bpy.context.scene.frame_end
                        half_point = num_frames / 2

                        old_frame = round(keyframe.frame_marker.frame + (self.old_offset/100)*num_frames)
                        new_frame = round(keyframe.frame_marker.frame + (self.new_offset/100)*num_frames)
                        if old_frame in keyframe_points:
                            self.work_queue.add(MoveKeyframeJob(keyframe_points[old_frame], new_frame))

                            old_half_frame = old_frame + half_point
                            new_half_frame = new_frame + half_point
                            if control.mirrored:
                                mirror_keyframe_points = {keyframe_point.co[0]:keyframe_point for keyframe_point in channel.mirror_fcurve.keyframe_points}
                                if old_half_frame in mirror_keyframe_points:
                                    self.work_queue.add(MoveKeyframeJob(mirror_keyframe_points[old_half_frame], new_half_frame))
                            else:
                                if old_half_frame in keyframe_points:
                                    self.work_queue.add(MoveKeyframeJob(keyframe_points[old_half_frame], new_half_frame))

                            old_end_frame = old_frame + num_frames
                            new_end_frame = new_frame + num_frames
                            if old_end_frame in keyframe_points:
                                self.work_queue.add(MoveKeyframeJob(keyframe_points[old_end_frame], new_end_frame))
                            self.work_queue.add(UpdateFCurveJob(channel.fcurve))  
                            if control.mirrored:
                                self.work_queue.add(UpdateFCurveJob(channel.mirror_fcurve))

class UpdateMarkerLengthJob(Job):
    def __init__(self):
        Job.__init__(self, "UPDATE_LENGTH")

    def work(self):
        num_animated_frames = bpy.context.scene.frame_end
        half_point = num_animated_frames / 2

        frame_markers = {frame_marker:id for id, frame_marker in enumerate(self.cycler.timings.frame_markers)}

        frame = 0.0
        for frame_marker in self.cycler.timings.frame_markers:
            frame_marker.frame = frame
            frame += (frame_marker.length/100.0) * num_animated_frames

        bpy.context.scene.timeline_markers.clear()
        for index, marker in enumerate(self.cycler.timings.frame_markers):
            marker_1 = bpy.context.scene.timeline_markers.new("{0} 1".format(marker.name), frame=marker.frame)
            marker_2 = bpy.context.scene.timeline_markers.new("{0} 2".format(marker.name), frame=marker.frame+half_point)
            if index == 0:
                marker_3 = bpy.context.scene.timeline_markers.new("{0} 1".format(marker.name), frame=num_animated_frames)

        #for control in self.cycler.controls:
        #    for channel in control:
        #        if channel.fcurve is None or (channel.control.mirrored and channel.mirror_fcurve is None):
        #            continue
        #        fcurve_keyframe_points = {keyframe_point.co[0]:keyframe_point for keyframe_point in channel.fcurve.keyframe_points}
        #        for keyframe in channel:
        #            old_frame = round(keyframe.frame_marker.old_frame + ((keyframe.offset/100)*num_animated_frames))
        #            new_frame = round(keyframe.frame_marker.frame + ((keyframe.offset/100)*num_animated_frames))
        #            if old_frame in fcurve_keyframe_points:
        #                self.work_queue.add(MoveKeyframeJob(fcurve_keyframe_points[old_frame], new_frame))
        #
        #                old_half_frame = old_frame + half_point
        #                new_half_frame = new_frame + half_point
        #                if control.mirrored:
        #                    mirror_fcurve_keyframe_points = {keyframe_point.co[0]:keyframe_point for keyframe_point in channel.mirror_fcurve.keyframe_points}
        #                    if old_half_frame in mirror_fcurve_keyframe_points:
        #                        self.work_queue.add(MoveKeyframeJob(mirror_fcurve_keyframe_points[old_half_frame], new_frame))
        #                else:
        #                    if old_half_frame in fcurve_keyframe_points:
        #                        self.work_queue.add(MoveKeyframeJob(fcurve_keyframe_points[old_half_frame], new_half_frame))
        #
        #                old_end_frame = old_frame + num_animated_frames
        #                new_end_frame = new_frame + num_animated_frames
        #                if old_end_frame in fcurve_keyframe_points:
        #                    self.work_queue.add(MoveKeyframeJob(fcurve_keyframe_points[old_end_frame], new_end_frame))
        #                self.work_queue.add(UpdateFCurveJob(channel.fcurve))  
        #                if control.mirrored:
        #                    self.work_queue.add(UpdateFCurveJob(channel.mirror_fcurve))

class FPSChangedJob(Job):
    def __init__(self, animation_length, old_fps, new_fps):
        Job.__init__(self, "FPS_CHANGED")
        self.animation_length = animation_length
        self.old_fps = old_fps
        self.new_fps = new_fps

    def work(self):
        job = ResizeAnimationJob(self.animation_length, self.animation_length, self.old_fps, self.new_fps)
        self.work_queue.add(job)
        bpy.context.scene.render.fps = self.new_fps

class AnimationLengthChangedJob(Job):
    def __init__(self, old_animation_length, new_animation_length, fps):
        Job.__init__(self, "ANIMATION_LENGTH_CHANGED")
        self.old_animation_length = old_animation_length
        self.new_animation_length = new_animation_length
        self.fps = fps

    def work(self):
        job = ResizeAnimationJob(self.old_animation_length, self.new_animation_length, self.fps, self.fps)
        self.work_queue.add(job)
        bpy.context.scene.frame_end = self.new_animation_length / self.fps

class AutoUpdateJob(Job):
    def __init__(self):
        Job.__init__(self, "AUTO_UPDATE")

    def work(self):
        anim_length = bpy.context.scene.frame_end
        half_point = anim_length / 2
        for control in self.cycler.controls:
            for channel in control:
                # Can't do anything if we need fcurves and can't find them
                if channel.fcurve is None or (control.mirrored and channel.mirror_fcurve is None):
                    continue

                fcurve_keyframe_points = {keyframe_point.co[0]:keyframe_point for keyframe_point in channel.fcurve.keyframe_points}
                
                expected_frames = []
                for keyframe in channel:
                    frame = round(keyframe.frame_marker.frame + ((keyframe.offset/100)*anim_length))   
                    expected_frames.append(frame)

                    # Add Initial Keyframe if it is missing, with a default value of 0.0
                    if not frame in fcurve_keyframe_points:
                        value = 0.0
                        if channel.type == "SCALE":
                            value = 1.0
                        self.work_queue.add(AddKeyframeJob(channel.fcurve, frame, value))                  

                    if not control.mirrored:
                        half_frame = round(frame + half_point)
                        expected_frames.append(half_frame)
                        if frame in fcurve_keyframe_points:

                            # Accumulate the values from the keyframe point
                            value = fcurve_keyframe_points[frame].co[1]
                            amplitude = fcurve_keyframe_points[frame].amplitude
                            back = fcurve_keyframe_points[frame].back
                            easing = fcurve_keyframe_points[frame].easing
                            left_handle_type = fcurve_keyframe_points[frame].handle_left_type
                            right_handle_type = fcurve_keyframe_points[frame].handle_right_type
                            left_handle = [round(fcurve_keyframe_points[frame].handle_left[0]+half_point), fcurve_keyframe_points[frame].handle_left[1]]
                            right_handle = [round(fcurve_keyframe_points[frame].handle_right[0]+half_point), fcurve_keyframe_points[frame].handle_right[1]]
                            interpolation = fcurve_keyframe_points[frame].interpolation
                            period = fcurve_keyframe_points[frame].period
                            type = fcurve_keyframe_points[frame].type

                            # Invert if we should
                            if keyframe.inverted:
                                value = -value
                                left_handle[1] = -left_handle[1]
                                right_handle[1] = -right_handle[1]

                            if half_frame in fcurve_keyframe_points:
                                # frame and half_frame both already exist
                                self.work_queue.add(ChangeKeyframeValueJob(fcurve_keyframe_points[half_frame], value,
                                    amplitude=amplitude, back=back, easing=easing, left_handle_type=left_handle_type, right_handle_type=right_handle_type,
                                    left_handle=left_handle, right_handle=right_handle, interpolation=interpolation, period=period, type=type))
                            else:
                                # frame exists but half_frame doesn't                                
                                self.work_queue.add(AddKeyframeJob(channel.fcurve, half_frame, value,
                                    amplitude=amplitude, back=back, easing=easing, left_handle_type=left_handle_type, right_handle_type=right_handle_type,
                                    left_handle=left_handle, right_handle=right_handle, interpolation=interpolation, period=period, type=type))
                        else:
                            # We are only missing the original frame
                            if half_frame in fcurve_keyframe_points:
                                self.work_queue.add(RemoveKeyframeJob(channel.fcurve, half_frame))
                            value = 0.0
                            if channel.type == "SCALE":
                                value = 1.0
                            self.work_queue.add(AddKeyframeJob(channel.fcurve, half_frame, value))

                if control.mirrored:
                    mirror_fcurve_keyframe_points = {keyframe_point.co[0]:keyframe_point for keyframe_point in channel.mirror_channel.fcurve.keyframe_points}
                    for keyframe in channel.mirror_channel:
                        frame = round(keyframe.frame_marker.frame + ((keyframe.offset/100)*anim_length))
                        half_frame = round(frame + half_point)
                        expected_frames.append(half_frame)
                        if frame in mirror_fcurve_keyframe_points:
                            
                            value = mirror_fcurve_keyframe_points[frame].co[1]
                            amplitude = mirror_fcurve_keyframe_points[frame].amplitude
                            back = mirror_fcurve_keyframe_points[frame].back
                            easing = mirror_fcurve_keyframe_points[frame].easing
                            left_handle_type = mirror_fcurve_keyframe_points[frame].handle_left_type
                            right_handle_type = mirror_fcurve_keyframe_points[frame].handle_right_type
                            left_handle = [round(mirror_fcurve_keyframe_points[frame].handle_left[0]+half_point), mirror_fcurve_keyframe_points[frame].handle_left[1]]
                            right_handle = [round(mirror_fcurve_keyframe_points[frame].handle_right[0]+half_point), mirror_fcurve_keyframe_points[frame].handle_right[1]]
                            interpolation = mirror_fcurve_keyframe_points[frame].interpolation
                            period = mirror_fcurve_keyframe_points[frame].period
                            type = mirror_fcurve_keyframe_points[frame].type

                            if channel.type == "LOCATION" and channel.axis == "X":
                                value = -value
                                left_handle[1] = -left_handle[1]
                                right_handle[1] = -right_handle[1]
                            elif channel.type == "ROTATION_EULER" and channel.axis in "YZ":
                                value = -value
                                left_handle[1] = -left_handle[1]
                                right_handle[1] = -right_handle[1]

                            if half_frame in fcurve_keyframe_points:
                                # frame and half_frame both already exist
                                self.work_queue.add(ChangeKeyframeValueJob(fcurve_keyframe_points[half_frame], value,
                                    amplitude=amplitude, back=back, easing=easing, left_handle_type=left_handle_type, right_handle_type=right_handle_type,
                                    left_handle=left_handle, right_handle=right_handle, interpolation=interpolation, period=period, type=type))
                            else:
                                # frame exists but half_frame doesn't                                
                                self.work_queue.add(AddKeyframeJob(channel.fcurve, half_frame, value,
                                    amplitude=amplitude, back=back, easing=easing, left_handle_type=left_handle_type, right_handle_type=right_handle_type,
                                    left_handle=left_handle, right_handle=right_handle, interpolation=interpolation, period=period, type=type))
                        else: # We are missing the mirror frame, so we just default the value
                            if half_frame in fcurve_keyframe_points:
                                self.work_queue.add(RemoveKeyframeJob(channel.fcurve, half_frame))
                            value = 0.0
                            if channel.type == "SCALE":
                                value = 1.0
                            self.work_queue.add(AddKeyframeJob(channel.fcurve, half_frame, value))

                frame = round(channel.keyframes.keyframes[0].frame_marker.frame + ((channel.keyframes.keyframes[0].offset/100)*anim_length))
                last_frame = round(frame + anim_length)
                expected_frames.append(last_frame)
                if frame in fcurve_keyframe_points:
                    value = fcurve_keyframe_points[frame].co[1]
                    amplitude = fcurve_keyframe_points[frame].amplitude
                    back = fcurve_keyframe_points[frame].back
                    easing = fcurve_keyframe_points[frame].easing
                    left_handle_type = fcurve_keyframe_points[frame].handle_left_type
                    right_handle_type = fcurve_keyframe_points[frame].handle_right_type
                    left_handle = [round(fcurve_keyframe_points[frame].handle_left[0]+anim_length), fcurve_keyframe_points[frame].handle_left[1]]
                    right_handle = [round(fcurve_keyframe_points[frame].handle_right[0]+anim_length), fcurve_keyframe_points[frame].handle_right[1]]
                    interpolation = fcurve_keyframe_points[frame].interpolation
                    period = fcurve_keyframe_points[frame].period
                    type = fcurve_keyframe_points[frame].type
                    if last_frame in fcurve_keyframe_points:
                        self.work_queue.add(ChangeKeyframeValueJob(fcurve_keyframe_points[last_frame], value,
                            amplitude=amplitude, back=back, easing=easing, left_handle_type=left_handle_type, right_handle_type=right_handle_type,
                            left_handle=left_handle, right_handle=right_handle, interpolation=interpolation, period=period, type=type))
                    else:
                        self.work_queue.add(AddKeyframeJob(channel.fcurve, last_frame, value,
                            amplitude=amplitude, back=back, easing=easing, left_handle_type=left_handle_type, right_handle_type=right_handle_type,
                            left_handle=left_handle, right_handle=right_handle, interpolation=interpolation, period=period, type=type))
                else:
                    if last_frame in fcurve_keyframe_points:
                        self.work_queue.add(RemoveKeyframeJob(channel.fcurve, last_frame))
                    value = 0.0
                    if channel.type == "SCALE":
                        value = 1.0
                    self.work_queue.add(AddKeyframeJob(channel.fcurve, last_frame, value))

                for frame in fcurve_keyframe_points:
                    if not frame in expected_frames:
                        self.work_queue.add(RemoveKeyframeJob(channel.fcurve, frame))
                self.work_queue.add(UpdateFCurveJob(channel.fcurve))
